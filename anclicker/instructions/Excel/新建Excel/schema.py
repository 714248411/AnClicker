"""Instruction parameter schema."""
from __future__ import annotations
from anclicker.domain.fields import FieldSpec
TYPE_ID = '新建Excel'
FIELDS = (FieldSpec('path', '保存路径', 'text', '', choices=(), minimum=0), FieldSpec('sheetName', '工作表名', 'text', 'Sheet1', choices=(), minimum=0))
