"""Instruction execution implementation."""
from __future__ import annotations
import shlex
from anclicker.instructions.common import actions
import subprocess
from anclicker.platform.services import open_path
from anclicker.domain.instructions import CommandRecord
from anclicker.domain.instructions import ExecutionContext
from anclicker.instructions.common import InstructionExecutorBase

class InstructionExecutor(InstructionExecutorBase):
    TYPE_ID = '运行外部文件'

    def execute_once(self, context: ExecutionContext, command: CommandRecord):
        if command.type_id != self.TYPE_ID:
            raise ValueError(f'运行外部文件执行器不能执行{command.type_id}')
        (delegated_, result_) = actions.delegated(context, self.TYPE_ID, command)
        if delegated_:
            return result_
        path_ = actions.substitute_variables(context, str(actions.parameter(command.parameters, '文件路径', '路径', default='')))
        arguments_ = str(actions.parameter(command.parameters, '参数', default='')).strip()
        if arguments_:
            process_ = subprocess.Popen([path_, *shlex.split(arguments_)])
            result_ = process_.pid
        else:
            open_path(path_)
            result_ = path_
        context.emit(f'运行外部文件：{path_}')
        return result_
