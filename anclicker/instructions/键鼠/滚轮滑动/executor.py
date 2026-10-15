"""Instruction execution implementation."""
from __future__ import annotations
from anclicker.instructions.common import actions
import random
from anclicker.domain.instructions import CommandRecord
from anclicker.domain.instructions import ExecutionContext
from anclicker.instructions.common import InstructionExecutorBase

from anclicker._imports import DeferredImports as _DeferredImports

# Dependencies declared here retain their existing on-demand loading boundaries.
_module_imports = _DeferredImports(globals(), {
    'scroll_event': ('from', 'anclicker.execution.recorded_input', ('scroll_event',), 0),
})


class InstructionExecutor(InstructionExecutorBase):
    TYPE_ID = '滚轮滑动'

    def execute_once(self, context: ExecutionContext, command: CommandRecord):
        if command.type_id != self.TYPE_ID:
            raise ValueError(f'滚轮滑动执行器不能执行{command.type_id}')
        (delegated_, result_) = actions.delegated(context, self.TYPE_ID, command)
        if delegated_:
            return result_
        p_ = command.parameters
        if actions.parameter(p_, '类型', default='滚轮滑动') == '随机滚轮滑动':
            distance_ = random.randint(int(actions.parameter(p_, '最小距离', default=1)), int(actions.parameter(p_, '最大距离', default=10)))
        else:
            distance_ = int(actions.parameter(p_, '距离', default=5))
        if actions.parameter(p_, '方向', default='向下') == '向下':
            distance_ = -distance_
        gui_ = actions.pyautogui_module()
        if p_.get('录制坐标'):
            gui_.moveTo(*actions.point(p_['录制坐标']), **actions.recording_options(command))
        if '录制滚轮' in p_:
            scroll_event = _module_imports.load('scroll_event')
            gui_.failSafeCheck()
            (dx_, dy_) = p_['录制滚轮']
            if not dx_ and float(dy_).is_integer():
                gui_.scroll(int(dy_), **actions.recording_options(command))
            else:
                scroll_event(context, dx_, dy_)
            return (dx_, dy_)
        gui_.scroll(distance_, **actions.recording_options(command))
        context.emit(f'滚轮滑动：{distance_}')
        return distance_
