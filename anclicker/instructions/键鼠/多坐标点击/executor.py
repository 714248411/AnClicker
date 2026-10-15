"""Instruction execution implementation."""
from __future__ import annotations
from anclicker.instructions.common import actions
import random
import math
import re
from anclicker.instructions.common import InstructionExecutorBase

def parse_points(value):
    if isinstance(value, (list, tuple)):
        parts = value
    else:
        parts = [part.strip() for part in re.split('[;；\\r\\n]+', str(value or '')) if part.strip()]
    if not parts:
        raise ValueError('请取点或填写坐标，例如 100,200; 300,400')
    try:
        return [actions.point(part) for part in parts]
    except (TypeError, ValueError, OverflowError) as error:
        raise ValueError('坐标格式应为 x,y；多个点用分号分隔') from error

class InstructionExecutor(InstructionExecutorBase):
    TYPE_ID = '多坐标点击'

    def execute_once(self, context, command):
        (delegated, result) = actions.delegated(context, self.TYPE_ID, command)
        if delegated:
            return result
        p = command.parameters
        raw = p.get('坐标列表', '')
        if isinstance(raw, str):
            raw = actions.substitute_variables(context, raw)
        points = parse_points(raw)
        action = p.get('动作', '左键单击')
        if action not in ('左键单击', '左键双击', '右键单击', '中键单击'):
            raise ValueError('请选择有效的点击方式')
        gap = float(p.get('间隔', 1))
        if not math.isfinite(gap) or not 0 <= gap <= 3600:
            raise ValueError('各点间隔应在 0～3600 秒之间')
        enabled = p.get('随机偏移', '关闭') == '启用'
        (rx, ry) = (int(p.get('水平偏移', 0)), int(p.get('垂直偏移', 0)))
        if not 0 <= rx <= 1000 or not 0 <= ry <= 1000:
            raise ValueError('随机偏移范围应在 0～1000 像素之间')
        clicked = []
        for (index, (x, y)) in enumerate(points):
            if not actions.wait_interruptibly(context, 0):
                break
            if enabled:
                x += random.randint(-rx, rx)
                y += random.randint(-ry, ry)
            actions.mouse_action(action, x, y, interval_=0.1)
            clicked.append((x, y))
            context.emit(f'多坐标点击：第 {index + 1}/{len(points)} 点，{x},{y}')
            if index + 1 < len(points) and (not actions.wait_interruptibly(context, gap)):
                break
        return clicked
