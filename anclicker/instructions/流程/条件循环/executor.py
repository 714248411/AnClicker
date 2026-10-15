"""Instruction execution implementation."""
from __future__ import annotations
from anclicker.instructions.common.flow_control import 条件循环Executor

class InstructionExecutor(条件循环Executor):
    CONSUMED_FIELDS = ('方式', '条件', '次数')
