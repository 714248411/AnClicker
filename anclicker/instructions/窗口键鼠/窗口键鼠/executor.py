"""Window-relative input with scoped binding and foreground restoration."""
from contextlib import contextmanager
from anclicker.instructions.common import InstructionExecutorBase, actions
from anclicker.platform.background_runtime import Windows, bind_background, close_background, current_backend
from .schema import OPERATIONS


class ScopedContext:
    def __init__(self, parent):
        self.parent = parent
        self.metadata = {key: value for key, value in parent.metadata.items()
                         if key not in ('_background_session', '_background_error',
                                        'recorded_keys', 'recorded_buttons', 'background_binding_profiles')}

    def __getattr__(self, name):
        return getattr(self.parent, name)


@contextmanager
def foreground(windows, target, context):
    gui = windows.gui
    hwnd = int(target['窗口句柄'])
    root = gui.GetAncestor(hwnd, 2) or hwnd
    previous = gui.GetForegroundWindow()
    placement = gui.GetWindowPlacement(root)
    topmost = bool(gui.GetWindowLong(root, -20) & 8)
    previous_above = gui.GetWindow(root, 3)  # GW_HWNDPREV
    try:
        if gui.IsIconic(root):
            gui.ShowWindow(root, 9)  # SW_RESTORE
        gui.SetWindowPos(root, -1, 0, 0, 0, 0, 3)  # HWND_TOPMOST, preserve geometry
        gui.SetForegroundWindow(root)
        actions.wait_interruptibly(context, 0.12)
        windows.validate(target)
        if gui.GetForegroundWindow() != root:
            raise RuntimeError('无法激活所选窗口，已取消输入')
        yield
    finally:
        if gui.IsWindow(root):
            restore = [lambda: gui.SetWindowPlacement(root, placement),
                       lambda: gui.SetWindowPos(root, -1 if topmost else -2, 0, 0, 0, 0, 19)]
            if (previous_above and gui.IsWindow(previous_above)
                    and bool(gui.GetWindowLong(previous_above, -20) & 8) == topmost):
                restore.append(lambda: gui.SetWindowPos(root, previous_above, 0, 0, 0, 0, 19))
            for operation in restore:
                try:
                    operation()
                except Exception as error:
                    context.emit('恢复窗口状态失败: ' + str(error))
        if previous and gui.IsWindow(previous):
            try:
                gui.SetForegroundWindow(previous)
            except Exception as error:
                context.emit('恢复原窗口焦点失败: ' + str(error))


def perform(api, windows, target, parameters, context, screen=False):
    operation = parameters.get('操作', '左键单击')
    if operation not in OPERATIONS and operation != '输入内容':
        raise ValueError('未知窗口键鼠操作')
    if context.stop_requested:
        raise RuntimeError('窗口键鼠已取消')
    windows.validate(target)
    def position(xkey, ykey):
        x, y = int(parameters.get(xkey, 0)), int(parameters.get(ykey, 0))
        width, height = windows.size(target)
        if not (0 <= x < width and 0 <= y < height):
            raise ValueError('坐标超出所选窗口内容区，请重新取点')
        return windows.gui.ClientToScreen(int(target['窗口句柄']), (x, y)) if screen else (x, y)
    if operation == '输入内容' or (operation == '组合键' and parameters.get('_窗口键盘')):
        from anclicker.instructions.窗口键鼠.窗口键盘.executor import keyboard_input
        keyboard_input(api, parameters, context, screen)
        return
    if operation == '组合键':
        keys = [key.strip().lower() for key in str(parameters.get('按键', '')).split('+') if key.strip()]
        if not keys:
            raise ValueError('请选择或填写按键')
        api.hotkey(*keys)
        return
    start = position('X', 'Y')
    end = position('结束X', '结束Y') if operation == '鼠标拖拽' else None
    api.moveTo(*start)
    if operation == '移动鼠标':
        return
    if operation == '鼠标拖拽':
        try:
            api.mouseDown(button='left')
            actions.wait_interruptibly(context, 0.1)
            api.moveTo(*end)
        finally:
            api.mouseUp(button='left')
    elif operation == '滚轮滑动':
        api.scroll(int(parameters.get('滚轮', 1)))
    else:
        button = {'右键单击': 'right', '中键单击': 'middle'}.get(operation, 'left')
        api.click(button=button, clicks=2 if operation == '左键双击' else 1, interval=0.1)


class InstructionExecutor(InstructionExecutorBase):
    TYPE_ID = '窗口键鼠'
    DEFAULT_OPERATION = '左键单击'
    perform = staticmethod(perform)

    def execute_once(self, context, command):
        parameters = dict(command.parameters)
        parameters.setdefault('操作', self.DEFAULT_OPERATION)
        parameters['_窗口键盘'] = self.TYPE_ID in ('窗口键盘', '窗口按下键盘', '窗口文本输入')
        target = parameters.get('窗口')
        if not isinstance(target, dict) or not target.get('窗口句柄'):
            raise ValueError('请先选择目标窗口')
        windows = (context.service('background_windows') or Windows)()
        target = windows.resolve(target)
        mode = parameters.get('模式', '前台')
        if mode == '后台':
            scoped = ScopedContext(context)
            try:
                binding = {key:parameters[key] for key in ('绑定方案','图像模式','鼠标模式','键盘模式','绑定模式','绑定等待') if key in parameters}
                binding.update(target)
                binding['启用截图'] = getattr(self, 'CAPTURE_ENABLED', False)
                bind_background(scoped, binding)
                self.perform(current_backend(scoped), windows, target, parameters, scoped)
            finally:
                close_background(scoped, keep_transport=not context.stop_requested)
        elif mode == '前台':
            import pyautogui
            with foreground(windows, target, context):
                self.perform(pyautogui, windows, target, parameters, context, screen=True)
        else:
            raise ValueError('请选择前台或后台模式')
        context.emit('窗口键鼠: ' + parameters.get('操作', '左键单击') + '完成')
