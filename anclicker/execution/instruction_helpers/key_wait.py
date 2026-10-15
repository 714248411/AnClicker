"""Cancellable key observation; remove only the listener owned by this wait."""
import sys
import threading

from anclicker.execution.actions import wait_interruptibly

from anclicker._imports import DeferredImports as _DeferredImports

# Dependencies declared here retain their existing on-demand loading boundaries.
_module_imports = _DeferredImports(globals(), {
    'keyboard': ('from', 'pynput', ('keyboard',), 0),
    'keyboard_2': ('import', 'keyboard', (), False),
})



def wait_for_key(context, key):
    if not wait_interruptibly(context, 0):
        return False
    triggered = threading.Event()
    if sys.platform == 'darwin':
        keyboard = _module_imports.load('keyboard')
        expected = getattr(keyboard.Key, key.lower(), None)

        def on_press(pressed):
            if ((expected is not None and pressed == expected)
                    or getattr(pressed, 'char', None) == key):
                triggered.set()
                return False

        listener = keyboard.Listener(on_press=on_press)
        listener.start()
        try:
            return _wait(context, triggered, listener)
        finally:
            listener.stop()
            listener.join(timeout=1)
    else:
        keyboard = _module_imports.load('keyboard_2')
        handle = keyboard.add_hotkey(key, triggered.set, suppress=False)
        try:
            return _wait(context, triggered)
        finally:
            keyboard.remove_hotkey(handle)


def _wait(context, triggered, listener=None):
    while wait_interruptibly(context, 0):
        if triggered.wait(.05):
            return wait_interruptibly(context, 0)
        if listener is not None and not listener.is_alive():
            raise RuntimeError('键盘监听已停止，请检查系统输入监控权限和桌面会话')
    return False
