"""Instruction parameter schema."""
from __future__ import annotations
from anclicker.domain.fields import FieldSpec
TYPE_ID = '获取Excel'
FIELDS = (FieldSpec('工作簿', '工作簿路径', 'path', '', required=True), FieldSpec('工作表', '工作表'), FieldSpec('单元格', '单元格', 'text', 'A1', required=True), FieldSpec('变量', '变量名称', 'text', 'Excel值', required=True), FieldSpec('递增', '按循环次数递增行', 'bool', False))
