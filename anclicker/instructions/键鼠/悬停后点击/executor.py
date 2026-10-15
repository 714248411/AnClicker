"""Instruction execution implementation."""
from __future__ import annotations
import math
from anclicker.execution.instruction_helpers.mouse_trajectory import wait_interruptibly
from anclicker.instructions.common import actions
from anclicker.execution.instruction_helpers.mouse_trajectory import trajectory
from anclicker.instructions.common import InstructionExecutorBase

class InstructionExecutor(InstructionExecutorBase):
    TYPE_ID = '悬停后点击'

    def execute_once(self, context, command):
        if command.type_id != self.TYPE_ID:
            raise ValueError('悬停后点击执行器收到错误的指令类型')
        (delegated, result) = actions.delegated(context, self.TYPE_ID, command)
        if delegated:
            return result
        p = command.parameters
        start = actions.point(p.get('悬停位置', '0,0'))
        end = actions.point(p.get('点击位置', '0,0'))
        times = [float(p.get(key, default)) for (key, default) in (('停留时间', 1.5), ('移动秒数', 1.0), ('点击前停留', 0.3))]
        if any((not math.isfinite(value) or not 0 <= value <= 3600 for value in times)):
            raise ValueError('停留和移动时间必须在 0 到 3600 秒之间')
        action = p.get('动作', '左键单击')
        clicks = {'左键单击': ('left', 1), '左键双击': ('left', 2), '右键单击': ('right', 1), '中键单击': ('middle', 1)}
        if action not in clicks:
            raise ValueError(f'不支持的点击动作：{action}')
        if context.stop_requested:
            return None
        gui = actions.pyautogui_module()
        gui.moveTo(*start, _pause=False)
        if not wait_interruptibly(context, times[0]):
            return None
        steps = max(1, math.ceil(times[1] / 0.02))
        for point in trajectory(start, end, steps):
            if context.stop_requested:
                return None
            gui.moveTo(*point, _pause=False)
            if not wait_interruptibly(context, times[1] / steps):
                return None
        if not wait_interruptibly(context, times[2]):
            return None
        (button, count) = clicks[action]
        for index in range(count):
            if context.stop_requested:
                return None
            gui.click(button=button, _pause=False)
            if index + 1 < count and (not wait_interruptibly(context, 0.1)):
                return None
        context.emit(f'悬停后点击：{start} → {end}（{action}）')
        return end
