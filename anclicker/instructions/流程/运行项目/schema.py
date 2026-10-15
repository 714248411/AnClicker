"""Instruction parameter schema."""
from __future__ import annotations
from anclicker.domain.fields import FieldSpec
TYPE_ID = '运行项目'
FIELDS = (FieldSpec('项目路径', '项目文件', required=True),)
