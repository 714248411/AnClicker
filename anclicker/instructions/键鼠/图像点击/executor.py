"""Instruction execution implementation."""
from __future__ import annotations
from anclicker.instructions.common import actions
from anclicker.domain.instructions import CommandRecord
from anclicker.domain.instructions import ExecutionContext
from anclicker.instructions.common import InstructionExecutorBase

class InstructionExecutor(InstructionExecutorBase):
    TYPE_ID = '图像点击'

    def execute_once(self, context: ExecutionContext, command: CommandRecord):
        if command.type_id != self.TYPE_ID:
            raise ValueError(f'图像点击执行器不能执行{command.type_id}')
        (delegated_, result_) = actions.delegated(context, self.TYPE_ID, command)
        if delegated_:
            return result_
        detection_only_ = command.parameters.get('动作') == '无操作'
        (skip_, timeout_) = actions.image_error_timeout(command.parameters)
        position_ = actions.click_image(command.parameters, context, min_search_time=timeout_)
        if context.stop_requested:
            return False
        if position_ is None:
            if skip_ and (not detection_only_):
                return False
            raise FileNotFoundError('未找到指定图像（图片存在判断未通过）' if detection_only_ else '未找到指定图像')
        (x_, y_) = position_
        label_ = '图片存在（无操作）' if detection_only_ else '图像点击'
        context.emit(f'{label_}：{x_},{y_}')
        return (x_, y_)
