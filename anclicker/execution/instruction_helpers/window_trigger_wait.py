"""Cancellable mouse/keyboard press trigger for window operations."""
import threading

def wait_for_trigger(context, parameters):
    from pynput import mouse, keyboard
    kind = parameters.get('触发按键', '中键')
    if kind not in ('左键','右键','中键','键盘按键','任意键盘按键'):
        raise ValueError('请选择有效触发按键')
    event = threading.Event()
    if kind == '任意键盘按键':
        listener = keyboard.Listener(on_press=lambda key: event.set())
    elif kind == '键盘按键':
        from anclicker.platform.background_runtime import BackgroundInput
        codes = parameters.get('触发键码') or [BackgroundInput._key(parameters.get('触发键', 'f8'))]
        if not isinstance(codes,list) or not codes or any(type(c) is not int or not 1 <= c <= 255 for c in codes):
            raise ValueError('请读取有效键盘按键')
        required, held = set(codes), set()
        def vk(key):
            value = getattr(key, 'value', key)
            return getattr(value, 'vk', None)
        def normalize(code):
            if code in (160,161) and 16 in required: return 16
            if code in (162,163) and 17 in required: return 17
            if code in (164,165) and 18 in required: return 18
            return code
        def press(key):
            held.add(normalize(vk(key)))
            if required <= held: event.set()
        def release(key):
            held.discard(normalize(vk(key)))

        listener = keyboard.Listener(on_press=press, on_release=release)
    else:
        button = {'左键':mouse.Button.left,'右键':mouse.Button.right,'中键':mouse.Button.middle}[kind]
        def click(x,y,pressed_button,pressed):
            if pressed_button == button and pressed: event.set()
        listener = mouse.Listener(on_click=click)
    if context.stop_requested: return False
    listener.start()
    try:
        context.emit('等待触发: ' + kind + '（按下后继续，可停止）')
        while not context.stop_requested:
            checkpoint = getattr(getattr(context,'runtime',None),'wait',None) or context.metadata.get('wait_interruptibly')
            if checkpoint and not checkpoint(0,context): return False
            if event.wait(0.05): return not context.stop_requested
            if not listener.is_alive(): raise RuntimeError('输入监听已停止，请检查权限')
        return False
    finally:
        listener.stop()
        listener.join(timeout=1)
