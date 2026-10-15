"""Instruction execution implementation."""
from __future__ import annotations
import time
from anclicker.instructions.common import actions
from anclicker.domain.instructions import CommandRecord
from anclicker.domain.instructions import ExecutionContext
from anclicker.instructions.common import InstructionExecutorBase

class InstructionExecutor(InstructionExecutorBase):
    TYPE_ID = '窗口焦点等待'

    def execute_once(self, context: ExecutionContext, command: CommandRecord):
        if command.type_id != self.TYPE_ID:
            raise ValueError(f'窗口焦点等待执行器不能执行{command.type_id}')
        (delegated_, result_) = actions.delegated(context, self.TYPE_ID, command)
        if delegated_:
            return result_
        p_ = command.parameters
        title_ = str(actions.parameter(p_, '标题包含', default=''))
        interval_ = float(actions.parameter(p_, '检测频率', default=0.2))
        deadline_ = time.monotonic() + float(actions.parameter(p_, '等待时间', default=30))
        wait_lost_ = actions.parameter(p_, '等待类型', default='获得焦点') == '失去焦点'
        gui_ = actions.pyautogui_module()
        while time.monotonic() <= deadline_:
            if not actions.wait_interruptibly(context, 0):
                return None
            active_ = title_ in str(gui_.getActiveWindowTitle() or '')
            if active_ != wait_lost_:
                context.emit(f'窗口焦点等待完成：{title_}')
                return True
            if not actions.wait_interruptibly(context, min(interval_, max(0, deadline_ - time.monotonic()))):
                return None
        raise TimeoutError(f'等待窗口焦点超时：{title_}')
