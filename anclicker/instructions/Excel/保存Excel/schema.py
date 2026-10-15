"""Instruction parameter schema."""
from __future__ import annotations
from anclicker.domain.fields import FieldSpec
TYPE_ID = '保存Excel'
FIELDS = (FieldSpec('path', '另存为(留空保存原文件)', 'text', '', choices=(), minimum=0),)
