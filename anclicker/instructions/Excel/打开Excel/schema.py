"""Instruction parameter schema."""
from __future__ import annotations
from anclicker.domain.fields import FieldSpec
TYPE_ID = '打开Excel'
FIELDS = (FieldSpec('sheetName', '工作表名(留空=第一个)', 'text', ''), FieldSpec('path', '文件路径', 'text', '', choices=(), minimum=0),)
