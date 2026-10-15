"""Instruction parameter schema."""
from __future__ import annotations
from anclicker.domain.fields import FieldSpec
TYPE_ID = '写入单元格'
FIELDS = (FieldSpec('工作簿', '工作簿路径', 'path', '', required=True), FieldSpec('工作表', '工作表'), FieldSpec('单元格', '单元格', 'text', 'A1', required=True), FieldSpec('递增', '按循环次数递增行', 'bool', False), FieldSpec('文本', '写入文本', 'multiline', ''))
