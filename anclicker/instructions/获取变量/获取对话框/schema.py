"""Instruction parameter schema."""
from __future__ import annotations
from anclicker.domain.fields import FieldSpec
TYPE_ID = '获取对话框'
FIELDS = (FieldSpec('标题', '对话框标题', 'text', '请输入'), FieldSpec('变量', '变量名称', 'text', '输入值', required=True), FieldSpec('提示', '提示内容', 'multiline', '请输入内容'))
