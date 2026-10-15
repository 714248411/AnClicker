"""Instruction execution implementation."""
from __future__ import annotations
from anclicker.instructions.common.local_ocr_instruction import LocalOcrExecutor

class InstructionExecutor(LocalOcrExecutor):
    TYPE_ID = 'OCR精准找字点击'
