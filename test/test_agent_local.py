import json,threading,time
from contextlib import nullcontext
from types import SimpleNamespace
from pathlib import Path
from unittest.mock import Mock
import pytest
from agent_local import LocalModelManager,launch_plans
from agent_service_lock import service_lock
from instructions.models import ExecutionContext


def test_two_managers_serialize_and_cancel_waiter(tmp_path,monkeypatch):
    first=LocalModelManager(tmp_path);second=LocalModelManager(tmp_path)
    for manager in (first,second):monkeypatch.setattr(manager,'ensure',lambda *_:'ready')
    context=ExecutionContext();finished=threading.Event();errors=[]
    def wait():
        try:
            with second.lease(context):pytest.fail('must not enter locked runtime')
        except InterruptedError:errors.append('cancelled')
        finally:finished.set()
    with first.lease(ExecutionContext()):
        thread=threading.Thread(target=wait);thread.start()
        assert not finished.wait(.2)
        context.stop_requested=True
        assert finished.wait(1)
        assert first.active==1
    thread.join()
    assert errors==['cancelled'] and second.active==0
    with second.lease(ExecutionContext()):assert second.active==1


def test_idle_release_does_not_interrupt_active_request(tmp_path,monkeypatch):
    manager=LocalModelManager(tmp_path,idle_seconds=1)
    monkeypatch.setattr(manager,'_alive',lambda:True)
    stop=Mock();monkeypatch.setattr(manager,'_stop_unlocked',stop)
    manager.active=1;manager.last_used=time.monotonic()-20
    manager._check_idle();stop.assert_not_called()
    manager.active=0;manager._check_idle();stop.assert_called_once()
    assert '空闲释放' in manager.status


def test_stop_cannot_interrupt_another_manager(tmp_path,monkeypatch):
    first=LocalModelManager(tmp_path);second=LocalModelManager(tmp_path)
    monkeypatch.setattr(first,'ensure',lambda *_:'ready')
    with first.lease(ExecutionContext()):
        with pytest.raises(RuntimeError,match='正在处理请求'):second.stop()


def test_unowned_state_is_not_removed_or_process_stopped(tmp_path):
    manager=LocalModelManager(tmp_path)
    state={'pid':123,'create_time':0};target=tmp_path/'service.json';target.write_text(json.dumps(state))
    manager._stop_unlocked()
    assert json.loads(target.read_text())==state


def test_failed_gpu_start_retries_cpu(tmp_path,monkeypatch):
    manager=LocalModelManager(tmp_path)
    (tmp_path/'qwen2.5-0.5b-instruct-q4_0.gguf').touch()
    gpu=tmp_path/'gpu.exe';gpu.touch();cpu=tmp_path/'cpu.exe';cpu.touch()
    monkeypatch.setattr('agent_local.launch_plans',lambda *args:[(gpu,[],'GPU'),(cpu,[],'CPU')])
    monkeypatch.setattr(manager,'gpu_available',lambda:True)
    monkeypatch.setattr(manager,'_adopt',lambda:None)
    launched=[]
    def launch(args,**kw):
        launched.append(args[0]);return SimpleNamespace(pid=len(launched),poll=lambda:7 if len(launched)==1 else None,returncode=7)
    monkeypatch.setattr('agent_local.subprocess.Popen',launch)
    monkeypatch.setattr('agent_local.psutil.Process',lambda pid:SimpleNamespace(pid=pid,create_time=lambda:1,is_running=lambda:True))
    monkeypatch.setattr(manager,'health',lambda:200 if len(launched)==2 else None)
    monkeypatch.setattr(manager,'_stop_unlocked',lambda:setattr(manager,'process',None))
    monkeypatch.setattr(manager,'_start_watcher',lambda:None)
    assert manager.ensure().startswith('CPU')
    assert launched==[str(gpu),str(cpu)]
    assert 'GPU' in manager.errors[0]


def test_cpu_only_and_busy_cpu_profiles(tmp_path,monkeypatch):
    monkeypatch.setattr('agent_local.psutil.virtual_memory',lambda:SimpleNamespace(available=8*1024**3))
    monkeypatch.setattr('agent_local.psutil.cpu_percent',lambda:90)
    monkeypatch.setattr('agent_local.psutil.cpu_count',lambda **kw:1)
    (tmp_path/'llama-vulkan').mkdir();(tmp_path/'llama-vulkan/llama-server.exe').touch()
    assert launch_plans(tmp_path,'auto',True)[0][2].startswith('GPU')
    plans=launch_plans(tmp_path,'auto',False)
    assert len(plans)==1 and plans[0][2].startswith('CPU')
    assert plans[0][1][plans[0][1].index('-t')+1]=='1'


def test_cancel_before_start_never_spawns(tmp_path,monkeypatch):
    launch=Mock();monkeypatch.setattr('agent_local.subprocess.Popen',launch)
    with pytest.raises(InterruptedError):LocalModelManager(tmp_path).ensure(ExecutionContext(stop_requested=True))
    launch.assert_not_called()


def test_lease_releases_lock_on_start_error(tmp_path,monkeypatch):
    manager=LocalModelManager(tmp_path)
    def fail(*a):raise RuntimeError('startup failed')
    monkeypatch.setattr(manager,'ensure',fail)
    with pytest.raises(RuntimeError):
        with manager.lease(ExecutionContext()):pass
    assert manager.active==0
    with service_lock(tmp_path,blocking=False) as acquired:assert acquired


def test_shared_file_lock_between_processes(tmp_path):
    import subprocess,sys
    code='from pathlib import Path;from agent_service_lock import service_lock;import sys\nwith service_lock(Path(sys.argv[1]),blocking=False) as locked:print(int(locked))'
    with service_lock(tmp_path):
        result=subprocess.run([sys.executable,'-c',code,str(tmp_path)],capture_output=True,text=True,check=True)
        assert result.stdout.strip()=='0'
    result=subprocess.run([sys.executable,'-c',code,str(tmp_path)],capture_output=True,text=True,check=True)
    assert result.stdout.strip()=='1'
