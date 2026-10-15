"""Instruction parameter schema."""
from __future__ import annotations
from anclicker.domain.fields import FieldSpec
TYPE_ID = '打开Excel'
FIELDS = (FieldSpec('path', '文件路径', 'text', '', choices=(), minimum=0),)
