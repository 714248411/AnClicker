"""Prepare one unbound helper off the UI thread and hand it to one execution."""
import atexit
import os
import threading
from instructions.models import ExecutionContext

_lock = threading.Lock()
_pending = None

def _configuration_key():
    from background_component_settings import config_path
    path = config_path()
    try:
        stat = path.stat()
        stamp = (stat.st_mtime_ns, stat.st_size)
    except OSError:
        stamp = None
    return (str(path), stamp, tuple(sorted((k, v) for k, v in os.environ.items() if k.startswith('ANCLICKER_DM_'))))

class Preparation:
    def __init__(self, factory, key):
        self.key = key
        self.context = ExecutionContext()
        self.done = threading.Event()
        self.lock = threading.Lock()
        self.transport = None
        self.error = None
        self.cancelled = False
        self.cleanup_thread = None
        self.thread = threading.Thread(target=self._run, args=(factory,), name='background-preload', daemon=True)
        self.thread.start()

    def _run(self, factory):
        transport = None
        try:
            transport = factory(self.context)
            with self.lock:
                if not self.cancelled:
                    self.transport, transport = transport, None
        except Exception as error:
            self.error = error
        finally:
            try:
                if transport is not None:
                    transport.close()
            finally:
                self.done.set()

    def cancel(self):
        with self.lock:
            self.cancelled = True
            self.context.stop_requested = True
            transport, self.transport = self.transport, None
        if transport is not None:
            self.cleanup_thread = threading.Thread(target=transport.close, name='background-preload-close', daemon=True)
            self.cleanup_thread.start()

    def take(self, context):
        while not self.done.wait(.05):
            if context.stop_requested:
                self.cancel()
                raise RuntimeError('后台准备已取消')
        with self.lock:
            if context.stop_requested or self.cancelled:
                transport = None
            else:
                transport, self.transport = self.transport, None
        if context.stop_requested or self.cancelled:
            self.cancel()
            raise RuntimeError('后台准备已取消')
        if self.error is not None:
            raise RuntimeError('后台组件准备失败：' + str(self.error)) from self.error
        if transport is not None:
            process = getattr(transport, 'process', None)
            if process is not None and process.poll() is not None:
                transport.close()
                return None
            transport.context = context
        return transport

def start_preload():
    global _pending
    from background_runtime import DmTransport
    key = _configuration_key()
    with _lock:
        if _pending is not None:
            if _pending.key == key and not (_pending.done.is_set() and _pending.error is not None):
                return
            _pending.cancel()
        _pending = Preparation(DmTransport, key)

def preload_status():
    with _lock:
        pending = _pending
    if pending is None:
        return '后台组件将在执行绑定时准备。'
    if not pending.done.is_set():
        return '正在提前加载后台组件，可继续选择窗口和填写参数…'
    if pending.error is not None:
        return '后台组件准备失败：' + str(pending.error)
    return '后台组件已就绪，等待执行时传入窗口参数。'

def take_preloaded(context):
    global _pending
    key = _configuration_key()
    with _lock:
        pending, _pending = _pending, None
    if pending is None:
        return None
    # Automatic setup can create the config during preparation. A missing original
    # config is allowed; explicit subsequent edits invalidate an existing config.
    if pending.key != key and (pending.key[1] is not None or pending.key[0] != key[0] or pending.key[2] != key[2]):
        pending.cancel()
        return None
    context.emit('正在接收预加载的后台组件…' if not pending.done.is_set() else '复用已预加载的后台组件')
    return pending.take(context)

def close_preload():
    global _pending
    with _lock:
        pending, _pending = _pending, None
    if pending is not None:
        pending.cancel()
        pending.thread.join(timeout=3)
        if pending.cleanup_thread is not None:
            pending.cleanup_thread.join(timeout=3)

atexit.register(close_preload)
