"""Private, authenticated loopback transport to the bundled yingdao execution engine."""
from __future__ import annotations
import atexit
from contextlib import contextmanager
from contextvars import ContextVar
import json
import os
from pathlib import Path
import queue
import subprocess
import sys
import threading
import time
import socket
import secrets
from anclicker.app.paths import resource_path, runtime_path
ROOT = resource_path()
class RpaBridge:
    def __init__(self, profile_name="rpa-browser"):
        self.profile_name = profile_name
        self.process = None
        self.lock = threading.RLock()
        self.messages = queue.Queue()
        self.sequence = 0
    def _reader(self, stream, messages):
        try:
            for line in stream:
                try:
                    message=json.loads(line)
                    if message.get('event')=='browser_chrome':
                        from anclicker.platform.browser_caption_theme import apply_browser_caption_theme
                        process=self.process
                        if process is not None and process.poll() is None:
                            apply_browser_caption_theme(process.pid,os.environ.get('ANCLICKER_UI_THEME','light'))
                        continue
                    messages.put(message)
                except ValueError:
                    pass
        except OSError:
            pass
        finally:
            messages.put({'error': '自动化执行引擎已退出'})
    def _start(self):
        if self.process is not None and self.process.poll() is None:
            return
        runtime_entry = ('Electron.app/Contents/MacOS/Electron' if sys.platform == 'darwin'
                         else 'electron.exe' if sys.platform == 'win32' else 'electron')
        executable = Path(os.environ.get('ANCLICKER_ELECTRON', runtime_path('electron') / runtime_entry))
        if not executable.is_file():
            raise RuntimeError('缺少自动化运行时，请运行 tools/setup_rpa_runtime.py 或设置 ANCLICKER_ELECTRON')
        environment = dict(os.environ)
        environment.pop('ELECTRON_RUN_AS_NODE', None)
        if sys.platform == 'linux' and getattr(sys, 'frozen', False):
            original = environment.get('LD_LIBRARY_PATH_ORIG')
            if original:
                environment['LD_LIBRARY_PATH'] = original
            else:
                environment.pop('LD_LIBRARY_PATH', None)
        environment['ANCLICKER_RPA_DATA'] = str(Path(os.environ.get('ANCLICKER_DATA_DIR', Path.home() / '.anclicker')) / self.profile_name)
        self.stream = None
        self.socket = None
        self.messages = queue.Queue()
        token = secrets.token_hex(32)
        listener = socket.socket()
        listener.bind(('127.0.0.1', 0))
        listener.listen(1)
        listener.settimeout(30)
        environment['ANCLICKER_RPA_PORT'] = str(listener.getsockname()[1])
        environment['ANCLICKER_RPA_TOKEN'] = token
        try:
            log_path = Path(environment['ANCLICKER_RPA_DATA']) / 'engine-startup.log'
            log_path.parent.mkdir(parents=True, exist_ok=True)
            with log_path.open('ab') as engine_log:
                self.process = subprocess.Popen([str(executable), str(ROOT / 'integrations/yingdao')],
                    stdin=subprocess.DEVNULL, stdout=subprocess.DEVNULL, stderr=engine_log,
                    env=environment, creationflags=subprocess.CREATE_NO_WINDOW if os.name == 'nt' else 0)
            self.socket, _ = listener.accept()
            self.socket.settimeout(30)
            self.stream = self.socket.makefile('rw', encoding='utf-8', newline='\n')
            if json.loads(self.stream.readline()).get('token') != token:
                raise RuntimeError('自动化引擎连接校验失败')
            self.socket.settimeout(None)
        except Exception:
            self.close()
            raise
        finally:
            listener.close()
        threading.Thread(target=self._reader, args=(self.stream, self.messages), daemon=True).start()
        try:
            message = self.messages.get(timeout=30)
        except queue.Empty as error:
            self.close()
            raise RuntimeError('自动化执行引擎启动超时') from error
        if not message.get('ready'):
            self.close()
            raise RuntimeError(message.get('error', '自动化执行引擎启动失败'))
    def execute(self, command, variables=None, context=None, timeout=180):
        with self.lock:
            if context is not None and context.stop_requested:
                raise InterruptedError('已停止自动化指令')
            self._start()
            if context is not None and context.stop_requested:
                self.close()
                raise InterruptedError('已停止自动化指令')
            self.sequence += 1
            request = {'id':self.sequence, 'command':command, 'variables':dict(variables or {}), 'theme':os.environ.get('ANCLICKER_UI_THEME')}
            self.stream.write(json.dumps(request, ensure_ascii=False, allow_nan=False) + '\n')
            self.stream.flush()
            deadline = time.monotonic() + timeout
            while time.monotonic() < deadline:
                if context is not None and context.stop_requested:
                    self.close()
                    raise InterruptedError('已停止自动化指令')
                try:
                    message = self.messages.get(timeout=0.1)
                except queue.Empty:
                    continue
                if message.get('id') not in (None, self.sequence):
                    continue
                for line in message.get('logs', []):
                    if context is not None:
                        context.emit(line)
                if message.get('event') == 'runtime_notice':
                    continue
                if message.get('error'):
                    raise RuntimeError(message['error'])
                return message
            self.close()
            raise TimeoutError('自动化指令超时，执行引擎已关闭')
    def set_theme(self, mode):
        """Update idle browser chrome without blocking a running command."""
        if mode not in ('light', 'dark') or not self.lock.acquire(blocking=False):
            return
        try:
            if self.process is not None and self.process.poll() is None and getattr(self, 'stream', None):
                self.stream.write(json.dumps({'operation': 'theme', 'theme': mode}) + '\n')
                self.stream.flush()
        except OSError:
            pass
        finally:
            self.lock.release()

    def close(self):
        with self.lock:
            process, self.process = self.process, None
            if process is None:
                return
            try:
                if process.poll() is None:
                    if getattr(self, 'stream', None):
                        self.stream.write('{"operation":"shutdown"}\n')
                        self.stream.flush()
                    else:
                        process.terminate()
                    process.wait(timeout=3)
            except (OSError, subprocess.TimeoutExpired):
                process.kill()
                process.wait(timeout=3)
            finally:
                if getattr(self, 'socket', None):
                    try:
                        self.socket.shutdown(socket.SHUT_RDWR)
                    except OSError:
                        pass
                    self.socket.close()
                if getattr(self, 'stream', None):
                    self.stream.close()

_bridge = RpaBridge()
atexit.register(_bridge.close)
_context_bridge = ContextVar('anclicker_rpa_bridge', default=None)


@contextmanager
def bridge_context(context):
    token = _context_bridge.set(context.metadata.get('rpa_bridge'))
    try:
        yield
    finally:
        _context_bridge.reset(token)


def get_bridge():
    return _context_bridge.get() or _bridge
