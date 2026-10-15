from anclicker.app.paths import get_install_folder
"""Resource-aware local inference: one managed service, GPU/CPU fallback and idle release."""
import json
import os
import re
import subprocess
import sys
import threading
import time
from contextlib import contextmanager
from pathlib import Path
import psutil
import requests
from anclicker.execution.agent_service_lock import service_lock

DEFAULT_URL='http://127.0.0.1:8766'

def runtime_root():
    if os.environ.get('ANCLICKER_AGENT_HOME'):return Path(os.environ['ANCLICKER_AGENT_HOME']).resolve()
    base=Path(sys.executable).parent if getattr(sys,'frozen',False) else Path(get_install_folder())
    return base/'.agent-runtime'

def launch_plans(root, profile='auto', gpu_available=False):
    """No free-RAM hard gate: mmap weights and bounded buffers permit paging."""
    if profile not in ('auto','cpu','gpu'):raise ValueError('未知运行模式')
    memory=psutil.virtual_memory().available
    cores=psutil.cpu_count(logical=False) or 2
    threads=max(1,min(4,cores-1 if cores>1 else 1))
    common=['-c','4096','-b','64','-ub','32','-t',str(threads),'--parallel','1','--jinja']
    cpu=(root/'llama-cpu/llama-server.exe',common+['-ngl','0'],'CPU · 低占用')
    gpu=(root/'llama-vulkan/llama-server.exe',common+['-ngl','99'],'GPU · Vulkan')
    use_gpu=gpu_available and gpu[0].is_file()
    if profile=='gpu':return ([gpu] if use_gpu else [])+[cpu]
    if profile=='cpu':return [cpu]+([gpu] if use_gpu else [])
    if use_gpu and (memory<2*1024**3 or psutil.cpu_percent()>75):return [gpu,cpu]
    return [cpu]+([gpu] if use_gpu else [])

class LocalModelManager:
    def __init__(self,root=None,idle_seconds=300):
        self.root=Path(root) if root else runtime_root()
        self.lock=threading.RLock();self.process=None;self.created=None
        self.profile='auto';self._applied_profile=None;self.idle_seconds=idle_seconds;self.active=0
        self.last_used=time.monotonic();self.status='模型尚未启动';self.errors=[]
        self._gpu=None;self._watcher=None;self.inference_gate=threading.Lock();self._observed_activity=0;self._lease_local=threading.local()
    @contextmanager
    def _exclusive(self,context=None,blocking=True):
        if getattr(self._lease_local,'depth',0):
            self._lease_local.depth+=1
            try:yield True
            finally:self._lease_local.depth-=1
            return
        with service_lock(self.root,context,blocking) as acquired:
            if acquired:self._lease_local.depth=1
            try:yield acquired
            finally:self._lease_local.depth=0
    def health(self):
        with requests.Session() as session:
            session.trust_env=False
            try:
                response=session.get(DEFAULT_URL+'/health',timeout=.5)
                return response.status_code
            except requests.RequestException:return None
    def gpu_available(self):
        if self._gpu is not None:return self._gpu
        binary=self.root/'llama-vulkan/llama-server.exe'
        if not binary.is_file():self._gpu=False;return False
        try:
            result=subprocess.run([str(binary),'--list-devices'],cwd=binary.parent,capture_output=True,timeout=15,creationflags=getattr(subprocess,'CREATE_NO_WINDOW',0))
            output=(result.stdout+result.stderr).decode('utf-8',errors='replace')
            available=[int(v) for v in re.findall(r'(\d+) MiB free',output)]
            self._gpu=result.returncode==0 and bool(re.search(r'Vulkan\d+:',output)) and (not available or max(available)>=768)
        except (OSError,subprocess.TimeoutExpired):self._gpu=False
        return self._gpu
    def _alive(self):
        if self.process is None:return False
        try:return self.process.is_running() and abs(self.process.create_time()-self.created)<.1
        except psutil.Error:return False
    def _adopt(self):
        """Only adopt a PID whose executable and creation time match our saved state."""
        try:
            state=json.loads((self.root/'service.json').read_text(encoding='utf-8'))
            process=psutil.Process(state['pid']);exe=Path(process.exe()).resolve()
            if exe not in {(self.root/'llama-cpu/llama-server.exe').resolve(),(self.root/'llama-vulkan/llama-server.exe').resolve()}:return
            if abs(process.create_time()-state['create_time'])>.1:return
            self.process=process;self.created=state['create_time'];self.status=state.get('status','本机模型运行中');self._applied_profile=state.get('profile','auto')
        except (OSError,ValueError,KeyError,psutil.Error):pass
    def _save(self):
        self._applied_profile=self.profile
        state={'pid':self.process.pid,'create_time':self.created,'status':self.status,'endpoint':DEFAULT_URL,'profile':self.profile,'idle_seconds':self.idle_seconds}
        target=self.root/'service.json';temporary=target.with_suffix('.tmp')
        temporary.write_text(json.dumps(state,ensure_ascii=False,indent=2),encoding='utf-8');temporary.replace(target)
    def _watch(self):
        while True:
            time.sleep(5)
            with self._exclusive(blocking=False) as acquired:
                if not acquired:continue
                self._check_idle()
                if self._watcher is None:return
    def _check_idle(self):
        with self.lock:
            if not self._alive():self._watcher=None;return
            try:
                modified=(self.root/'activity').stat().st_mtime
                if modified>self._observed_activity:self.last_used=time.monotonic();self._observed_activity=modified
            except OSError:pass
            if self.active==0 and time.monotonic()-self.last_used>=self.idle_seconds:
                self._stop_unlocked();self.status='模型已空闲释放，下次请求自动启动';self._watcher=None;return
    def _start_watcher(self):
        if self._watcher is None:
            self._watcher=threading.Thread(target=self._watch,daemon=True,name='AnClicker-model-idle');self._watcher.start()
    def ensure(self,context=None,profile=None):
        with self._exclusive(context),self.lock:
            if context is not None and context.stop_requested:raise InterruptedError('已停止')
            if profile:self.profile=profile
            if not self._alive():
                self.process=None;self.created=None;self._adopt()
            health=self.health()
            if health==200 and self._alive() and self.profile!='auto' and self.profile!=self._applied_profile:
                self._stop_unlocked();health=None
            if health==200:
                self.last_used=time.monotonic()
                if self._alive():self._start_watcher()
                return self.status if self._alive() else '已连接现有本地服务'
            if health is not None and not self._alive():raise RuntimeError('8766 端口的服务正在加载或异常，请稍后检测')
            if self._alive():self._stop_unlocked()
            if sys.platform!='win32':raise RuntimeError('内置模型运行器目前支持 Windows x64；本平台请在设置中连接 Ollama 或兼容模型服务')
            model=self.root/'qwen2.5-0.5b-instruct-q4_0.gguf'
            if not model.is_file():raise RuntimeError('请先准备本机模型：运行 tools/prepare_agent_models.py --gpu')
            self.errors=[]
            for binary,options,label in launch_plans(self.root,self.profile,self.gpu_available()):
                if not binary.is_file():self.errors.append(label+' 缺少运行器');continue
                if context is not None and context.stop_requested:raise InterruptedError('已停止')
                self.status='正在加载 '+label
                try:
                    with (self.root/'server.log').open('ab') as log:
                        child=subprocess.Popen([str(binary),'-m',str(model),'--host','127.0.0.1','--port','8766','--alias','anclicker-small',*options],cwd=binary.parent,
                            stdin=subprocess.DEVNULL,stdout=log,stderr=log,creationflags=getattr(subprocess,'CREATE_NO_WINDOW',0))
                    self.process=psutil.Process(child.pid);self.created=self.process.create_time()
                    deadline=time.monotonic()+90
                    while time.monotonic()<deadline:
                        if context is not None and context.stop_requested:raise InterruptedError('已停止')
                        if child.poll() is not None:
                            code=child.returncode
                            suffix='，请更新 Visual C++ x64 运行库或重新准备便携运行器' if code in (3221225477,-1073741819) else ''
                            raise RuntimeError(f'运行器退出 {code}'+suffix)
                        if self.health()==200:
                            self.status=label+' · 已就绪';self.last_used=time.monotonic();self._save();self._start_watcher();return self.status
                        time.sleep(.2)
                    raise TimeoutError('启动超过 90 秒')
                except InterruptedError:
                    self._stop_unlocked();raise
                except Exception as error:
                    self.errors.append(label+'：'+str(error));self._stop_unlocked()
            self.status='启动失败';raise RuntimeError('；'.join(self.errors)+'。详情见 .agent-runtime/server.log')
    def _stop_unlocked(self):
        owned_pid=self.process.pid if self.process is not None else None
        owned_created=self.created
        if self._alive():
            self.process.terminate()
            try:self.process.wait(3)
            except psutil.TimeoutExpired:self.process.kill();self.process.wait(3)
        self.process=None;self.created=None
        try:
            saved=json.loads((self.root/'service.json').read_text(encoding='utf-8'))
            if saved.get('pid')==owned_pid and saved.get('create_time')==owned_created:
                (self.root/'service.json').unlink(missing_ok=True)
        except (OSError,ValueError):pass
    def stop(self,adopt=True):
        with self._exclusive(blocking=False) as acquired:
            if not acquired:raise RuntimeError('模型正在处理请求，请先停止当前 Agent 请求')
            with self.lock:
                if self.active:raise RuntimeError('请先停止当前 Agent 请求')
                if adopt and not self._alive():self._adopt()
                self._stop_unlocked();self.status='本机模型已停止'
    @contextmanager
    def lease(self,context,profile='auto',idle_seconds=300):
        # Count requests before startup, so the idle watcher cannot race inference.
        while not self.inference_gate.acquire(timeout=.1):
            if context.stop_requested:raise InterruptedError('已停止等待模型')
        try:
            with self._exclusive(context):
                with self.lock:self.active+=1;self.profile=profile;self.idle_seconds=idle_seconds
                try:
                    (self.root/'activity').touch()
                    self.ensure(context);yield
                finally:
                    with self.lock:self.active-=1;self.last_used=time.monotonic()
                    (self.root/'activity').touch()
        finally:self.inference_gate.release()
    def snapshot(self):
        acquired=self.lock.acquire(blocking=False)
        try:
            rss=0
            if acquired and self._alive():
                try:rss=round(self.process.memory_info().rss/1024**2)
                except psutil.Error:pass
            return {'status':self.status,'active_requests':self.active,'memory_mb':rss,'idle_seconds':self.idle_seconds,'profile':self.profile}
        finally:
            if acquired:self.lock.release()

_manager=LocalModelManager()
def start_local_model(profile='auto',context=None,idle_seconds=None):
    if idle_seconds is not None:_manager.idle_seconds=max(30,min(3600,int(idle_seconds)))
    return _manager.ensure(context,profile)
def stop_local_model(adopt=True):_manager.stop(adopt)
def local_model_lease(context,profile='auto',idle_seconds=300):return _manager.lease(context,profile,idle_seconds)

def retry_on_cpu(context):
    with _manager._exclusive(context),_manager.lock:
        if not _manager._alive() or not _manager.status.startswith('GPU'):return False
        _manager._stop_unlocked()
        _manager.ensure(context,'cpu')
    return True
