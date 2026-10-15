"""Instruction execution implementation."""
from __future__ import annotations
from anclicker.instructions.common.flow_control import 条件判断Executor

class InstructionExecutor(条件判断Executor):
    CONSUMED_FIELDS = ('条件',)
