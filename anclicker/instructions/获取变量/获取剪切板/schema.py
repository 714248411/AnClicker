"""Instruction parameter schema."""
from __future__ import annotations
from anclicker.domain.fields import FieldSpec
TYPE_ID = '获取剪切板'
FIELDS = (FieldSpec('变量', '变量名称', 'text', '剪切板', required=True),)
