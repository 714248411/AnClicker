from anclicker.instructions.窗口键鼠.窗口键鼠.executor import InstructionExecutor as BaseExecutor
from anclicker.platform.background_runtime import BackgroundInput
from anclicker.instructions.common import actions


def keyboard_input(api, parameters, context, screen=False):
    if parameters.get('操作', '组合键') == '输入内容':
        text = actions.substitute_variables(context, str(parameters.get('内容', '')))
        if screen:
            from pynput.keyboard import Controller
            keyboard = Controller()
            for character in text:
                if context.stop_requested:
                    raise RuntimeError('键盘输入已取消')
                keyboard.type(character)
        else:
            api.write(text)
        return
    codes = parameters.get('按键码')
    if not codes:
        names = [key.strip() for key in str(parameters.get('按键', '')).split('+') if key.strip()]
        codes = [BackgroundInput._key(key) for key in names]
    if not isinstance(codes, list) or not codes or any(type(code) is not int or not 1 <= code <= 255 or code == 231 for code in codes):
        raise ValueError('请读取或填写有效按键；文字请使用输入内容')
    pressed = []
    try:
        for code in codes:
            if context.stop_requested:
                raise RuntimeError('键盘输入已取消')
            pressed.append(code)
            if screen:
                native_key(code, False)
            else:
                api.keyDown('win32:' + str(code))
    finally:
        cleanup_error = None
        for code in reversed(pressed):
            try:
                if screen:
                    native_key(code, True)
                else:
                    api.keyUp('win32:' + str(code))
            except Exception as error:
                cleanup_error = cleanup_error or error
        if cleanup_error is not None:
            raise cleanup_error


def native_key(code, up):
    import win32api
    extended = code in (33, 34, 35, 36, 37, 38, 39, 40, 44, 45, 46, 91, 92, 93, 111, 144, 163, 165)
    win32api.keybd_event(code, win32api.MapVirtualKey(code, 0), (2 if up else 0) | (1 if extended else 0), 0)


class InstructionExecutor(BaseExecutor):
    TYPE_ID = '窗口键盘'
    DEFAULT_OPERATION = '组合键'

    def execute_once(self, context, command):
        if command.parameters.get('操作', '组合键') not in ('组合键', '输入内容'):
            raise ValueError('该操作不属于窗口键盘')
        return super().execute_once(context, command)
