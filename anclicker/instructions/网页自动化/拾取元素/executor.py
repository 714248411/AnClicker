"""Instruction execution implementation."""
from __future__ import annotations
from anclicker.instructions.common.rpa_instruction import RpaInstructionExecutor

class InstructionExecutor(RpaInstructionExecutor):
    TYPE_ID = '拾取元素'
    COMMAND_ID = 'pickElement'
