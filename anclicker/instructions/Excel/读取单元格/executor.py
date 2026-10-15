"""Instruction execution implementation."""
from __future__ import annotations
from anclicker.instructions.common.rpa_instruction import RpaInstructionExecutor

class InstructionExecutor(RpaInstructionExecutor):
    TYPE_ID = '读取单元格'
    COMMAND_ID = 'excelRead'
