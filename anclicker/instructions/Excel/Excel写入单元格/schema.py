"""Instruction parameter schema."""
from __future__ import annotations
from anclicker.domain.fields import FieldSpec
TYPE_ID = 'Excel写入单元格'
FIELDS = (FieldSpec('cell', '单元格(如A1)', 'text', 'A1', choices=(), minimum=0), FieldSpec('value', '写入内容', 'text', '', choices=(), minimum=0))
