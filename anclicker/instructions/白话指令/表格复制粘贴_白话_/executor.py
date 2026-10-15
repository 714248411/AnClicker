"""Instruction execution implementation."""
from __future__ import annotations
from anclicker.instructions.common.rpa_instruction import RpaInstructionExecutor

class InstructionExecutor(RpaInstructionExecutor):
    TYPE_ID = '表格复制粘贴（白话）'
    COMMAND_ID = 'excelTableCopyPaste'
