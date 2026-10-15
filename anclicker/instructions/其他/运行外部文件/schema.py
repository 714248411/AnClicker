"""Instruction parameter schema."""
from __future__ import annotations
from anclicker.domain.fields import FieldSpec
TYPE_ID = '运行外部文件'
FIELDS = (FieldSpec('文件路径', '文件路径', 'path', '', required=True), FieldSpec('参数', '启动参数'))
