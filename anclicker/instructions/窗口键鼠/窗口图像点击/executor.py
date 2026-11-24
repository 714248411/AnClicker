from anclicker.instructions.键鼠.图像点击.executor import InstructionExecutor as BaseExecutor

class InstructionExecutor(BaseExecutor):
    TYPE_ID = '窗口图像点击'

    def execute_once(self, context, command):
        target = command.parameters.get('区域窗口')
        if command.parameters.get('区域模式') != '跟随窗口' or not isinstance(target, dict) or not target.get('窗口句柄'):
            raise ValueError('窗口图像点击需要先选择目标窗口')
        return super().execute_once(context, command)
