"""Instruction execution implementation."""
from __future__ import annotations
from anclicker.instructions.common import actions
from anclicker.domain.instructions import CommandRecord
from anclicker.domain.instructions import ExecutionContext
from anclicker.instructions.common import InstructionExecutorBase

class InstructionExecutor(InstructionExecutorBase):
    TYPE_ID = '多图点击'

    def execute_once(self, context: ExecutionContext, command: CommandRecord):
        if command.type_id != self.TYPE_ID:
            raise ValueError(f'多图点击执行器不能执行{command.type_id}')
        (delegated_, result_) = actions.delegated(context, self.TYPE_ID, command)
        if delegated_:
            return result_
        paths_ = str(actions.parameter(command.parameters, '图像路径', default='')).replace(';', '\n').replace('、', '\n').splitlines()
        for path_ in (item_.strip() for item_ in paths_ if item_.strip()):
            parameters_ = dict(command.parameters)
            parameters_['图像路径'] = path_
            position_ = actions.click_image(parameters_, context)
            if context.stop_requested:
                return False
            if position_ is not None:
                context.emit(f'多图点击命中：{path_}')
                return path_
        if actions.parameter(command.parameters, '异常', default='自动略过') in {'自动跳过', '自动略过'}:
            return False
        raise FileNotFoundError('未找到任一指定图像')
