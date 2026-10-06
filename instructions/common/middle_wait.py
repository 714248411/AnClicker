"""Cancellable global middle-button observation (Windows/macOS/X11)."""
import importlib
import threading


def wait_for_middle(context):
    if context.stop_requested:
        return False
    mouse = importlib.import_module('pynput.mouse')
    triggered = threading.Event()

    def on_click(x, y, button, pressed):
        # Activate on release, so the physical middle button is no longer held
        # when the optional synthetic left click is sent.
        if button == mouse.Button.middle and not pressed:
            triggered.set()

    listener = mouse.Listener(on_click=on_click)
    listener.start()
    try:
        context.emit('等待鼠标中键点击并松开；可停止或取消测试')
        while not context.stop_requested:
            checkpoint = context.metadata.get('wait_interruptibly')
            if checkpoint is not None and not checkpoint(0, context):
                return False
            if triggered.wait(0.05):
                return not context.stop_requested
            if not listener.is_alive():
                raise RuntimeError('鼠标监听已停止，请检查系统输入监控权限和桌面会话')
        return False
    finally:
        listener.stop()
        listener.join(timeout=1)
