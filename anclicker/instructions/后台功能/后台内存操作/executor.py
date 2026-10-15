"""Instruction execution implementation."""
from __future__ import annotations
from anclicker.instructions.common.background_instruction import BackgroundExecutor

class InstructionExecutor(BackgroundExecutor):
    TYPE_ID = '后台内存操作'
