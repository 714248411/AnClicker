"""Instruction execution implementation."""
from __future__ import annotations
from anclicker.instructions.common.rpa_instruction import RpaInstructionExecutor

class InstructionExecutor(RpaInstructionExecutor):
    TYPE_ID = '坐标点击（可多点）'
    COMMAND_ID = 'clickXY'
