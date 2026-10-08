"""Cancellable key observation; remove only the listener owned by this wait."""
import sys
import threading

from instructions.common.actions import wait_interruptibly


def wait_for_key(context, key):
    if not wait_interruptibly(context, 0):
        return False
    triggered = threading.Event()
    if sys.platform == 'darwin':
        from pynput import keyboard
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
        import keyboard
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
