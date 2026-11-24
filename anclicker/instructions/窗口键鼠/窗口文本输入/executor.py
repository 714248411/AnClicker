from anclicker.instructions.窗口键鼠.窗口键盘.executor import InstructionExecutor as BaseExecutor, keyboard_input
from anclicker.instructions.窗口键鼠.窗口键鼠.executor import perform
from anclicker.instructions.common import actions

class InstructionExecutor(BaseExecutor):
    TYPE_ID = '窗口文本输入'
    DEFAULT_OPERATION = '输入内容'

    @staticmethod
    def perform(api, windows, target, parameters, context, screen=False):
        if 'X' not in parameters or 'Y' not in parameters:
            raise ValueError('请重新设置窗口文本输入的输入位置')
        perform(api, windows, target, dict(parameters, 操作='左键单击'), context, screen)
        actions.wait_interruptibly(context, 0.15)
        if context.stop_requested:
            raise RuntimeError('窗口文本输入已取消')
        keyboard_input(api, dict(parameters, 操作='输入内容'), context, screen)
