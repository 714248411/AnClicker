"""Instruction execution implementation."""
from __future__ import annotations
from anclicker.instructions.common import actions
import subprocess
from models.cmd_commands import normalize_cmd_paths
from anclicker.domain.instructions import CommandRecord
from anclicker.domain.instructions import ExecutionContext
from anclicker.instructions.common import InstructionExecutorBase

class InstructionExecutor(InstructionExecutorBase):
    TYPE_ID = '运行cmd'

    def execute_once(self, context: ExecutionContext, command: CommandRecord):
        if command.type_id != self.TYPE_ID:
            raise ValueError(f'运行cmd执行器不能执行{command.type_id}')
        (delegated_, result_) = actions.delegated(context, self.TYPE_ID, command)
        if delegated_:
            return result_
        command_ = actions.substitute_variables(context, str(actions.parameter(command.parameters, '命令', '内容', default='')))
        command_=normalize_cmd_paths(command_)
        if actions.parameter(command.parameters, '等待完成', default=True):
            result_ = actions.run_process(command_, shell_=True)
            context.emit(result_.stdout.rstrip())
            return result_.returncode
        process_ = subprocess.Popen(command_, shell=True, creationflags=getattr(subprocess, 'CREATE_NO_WINDOW', 0))
        context.emit(f'运行cmd：PID {process_.pid}')
        return process_.pid
