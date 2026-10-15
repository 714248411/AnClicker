"""Instruction parameter schema."""
from __future__ import annotations
from anclicker.domain.fields import FieldSpec
TYPE_ID = '文本输入'
FIELDS = (FieldSpec('内容', '输入内容', 'multiline', '', required=True), FieldSpec('手动输入', '特殊控件手动输入', 'bool', False))
