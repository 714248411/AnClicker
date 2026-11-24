import math
from anclicker.instructions.窗口键鼠.窗口键鼠.executor import InstructionExecutor as BaseExecutor, perform
from anclicker.instructions.common import actions

class InstructionExecutor(BaseExecutor):
    TYPE_ID = '窗口悬停后点击'

    @staticmethod
    def perform(api, windows, target, parameters, context, screen=False):
        delay = float(parameters.get('停留时间', 1.5))
        if not math.isfinite(delay) or not 0 <= delay <= 3600:
            raise ValueError('停留时间必须在 0–3600 秒之间')
        end = dict(parameters, X=int(parameters.get('结束X',0)), Y=int(parameters.get('结束Y',0)))
        width, height = windows.size(target)
        if not 0 <= end['X'] < width or not 0 <= end['Y'] < height:
            raise ValueError('点击坐标超出窗口内容区')
        perform(api, windows, target, dict(parameters, 操作='移动鼠标'), context, screen)
        actions.wait_interruptibly(context, delay)
        perform(api, windows, target, end, context, screen)
