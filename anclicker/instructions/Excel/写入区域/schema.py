"""Instruction parameter schema."""
from __future__ import annotations
from anclicker.domain.fields import FieldSpec
TYPE_ID = '写入区域'
FIELDS = (FieldSpec('range', '起始单元格(如A1)', 'text', 'A1', choices=(), minimum=0), FieldSpec('data', '数据(变量名,二维数组)', 'text', '变量1', choices=(), minimum=0))
