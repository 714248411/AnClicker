"""Instruction parameter schema."""
from __future__ import annotations
from anclicker.domain.fields import FieldSpec
TYPE_ID = '获取鼠标位置'
FIELDS = (FieldSpec('变量', '变量名称', 'text', '鼠标位置', required=True),)
