"""Instruction parameter schema."""
from __future__ import annotations
from anclicker.domain.fields import FieldSpec
TYPE_ID = '读取单元格'
FIELDS = (FieldSpec('cell', '单元格(如A1)', 'text', 'A1', choices=(), minimum=0), FieldSpec('varName', '保存到变量', 'text', '变量1', choices=(), minimum=0))
