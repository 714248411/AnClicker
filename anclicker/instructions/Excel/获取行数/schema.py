"""Instruction parameter schema."""
from __future__ import annotations
from anclicker.domain.fields import FieldSpec
TYPE_ID = '获取行数'
FIELDS = (FieldSpec('varName', '保存到变量', 'text', '行数', choices=(), minimum=0),)
