"""Instruction parameter schema."""
from __future__ import annotations
from anclicker.domain.instruction_fields.local_ocr_instruction import fields_for
TYPE_ID = 'OCR精准找字点击'
FIELDS = fields_for(TYPE_ID)
