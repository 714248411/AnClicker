"""Instruction parameter schema."""
from __future__ import annotations
from anclicker.domain.fields import FieldSpec
TYPE_ID = '抓取导出Excel'
FIELDS = (FieldSpec('varName', '数据变量(二维数组)', 'text', '抓取列表', choices=(), minimum=0), FieldSpec('path', '保存路径(留空存桌面)', 'text', '', choices=(), minimum=0))
