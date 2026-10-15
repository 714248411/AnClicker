"""Instruction parameter schema."""
from __future__ import annotations
from anclicker.domain.fields import FieldSpec
TYPE_ID = '读取区域'
FIELDS = (FieldSpec('range', '区域(如A1:C5)', 'text', 'A1:C5', choices=(), minimum=0), FieldSpec('varName', '保存到变量(二维数组)', 'text', '变量1', choices=(), minimum=0))
