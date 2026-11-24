import math
from anclicker.instructions.窗口键鼠.窗口键鼠.executor import InstructionExecutor as BaseExecutor, perform
from anclicker.instructions.common import actions
from .schema import OPERATIONS


def validate_points(parameters):
    points = parameters.get('坐标列表')
    if not isinstance(points, list) or not points:
        raise ValueError('请至少添加一个坐标')
    if any(not isinstance(point, (list, tuple)) or len(point) != 2 or
           any(type(value) is not int or value < 0 for value in point) for point in points):
        raise ValueError('坐标必须是非负整数 X、Y')
    interval = float(parameters.get('间隔', 0.2))
    if not math.isfinite(interval) or not 0 <= interval <= 3600:
        raise ValueError('点击间隔必须在 0–3600 秒之间')
    if parameters.get('操作', '左键单击') not in OPERATIONS:
        raise ValueError('请选择有效点击方式')
    return points, interval


class InstructionExecutor(BaseExecutor):
    TYPE_ID = '窗口多坐标点击'

    def execute_once(self, context, command):
        validate_points(command.parameters)
        return super().execute_once(context, command)

    @staticmethod
    def perform(api, windows, target, parameters, context, screen=False):
        points, interval = validate_points(parameters)
        width, height = windows.size(target)
        if any(x >= width or y >= height for x, y in points):
            raise ValueError('坐标超出所选窗口内容区，请检查坐标列表')
        for index, (x, y) in enumerate(points):
            if index:
                actions.wait_interruptibly(context, interval)
            if context.stop_requested:
                raise RuntimeError('窗口多坐标点击已取消')
            perform(api, windows, target, dict(parameters, X=x, Y=y), context, screen)
