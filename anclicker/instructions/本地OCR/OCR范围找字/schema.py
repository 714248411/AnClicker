"""Instruction parameter schema."""
from __future__ import annotations
from anclicker.domain.instruction_fields.local_ocr_instruction import fields_for
TYPE_ID = 'OCR范围找字'
FIELDS = fields_for(TYPE_ID)
