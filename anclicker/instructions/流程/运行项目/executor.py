"""Instruction execution implementation."""
from __future__ import annotations
from anclicker.instructions.common import actions
from anclicker.instructions.common import InstructionExecutorBase

class InstructionExecutor(InstructionExecutorBase):
    TYPE_ID = '运行项目'
    CONSUMED_FIELDS = ('项目路径',)

    def execute_once(self, context, command):
        if context.stop_requested:
            return None
        (handled, result) = actions.delegated(context, self.TYPE_ID, command)
        if handled:
            return result
        runner = getattr(getattr(context, 'runtime', None), 'run_project', None) or context.metadata.get('run_project')
        if runner is None:
            raise RuntimeError('请保存运行项目指令后，在主界面启动或使用单行运行')
        path = actions.substitute_variables(context, str(command.parameters.get('项目路径', '')))
        return runner(path, context)
