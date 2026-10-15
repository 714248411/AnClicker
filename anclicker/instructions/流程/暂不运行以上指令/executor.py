"""Instruction execution implementation."""
from __future__ import annotations
from anclicker.instructions.common import actions
from anclicker.instructions.common import InstructionExecutorBase

class InstructionExecutor(InstructionExecutorBase):
    TYPE_ID = '暂不运行以上指令'

    def execute_once(self, context, command):
        (delegated, result) = actions.delegated(context, self.TYPE_ID, command)
        return result if delegated else None
