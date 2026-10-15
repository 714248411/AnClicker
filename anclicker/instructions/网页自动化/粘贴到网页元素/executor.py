"""Instruction execution implementation."""
from __future__ import annotations
from anclicker.instructions.common.rpa_instruction import RpaInstructionExecutor

class InstructionExecutor(RpaInstructionExecutor):
    TYPE_ID = '粘贴到网页元素'
    COMMAND_ID = 'pasteToElement'
