"""Instruction parameter schema."""
from __future__ import annotations
from anclicker.domain.fields import FieldSpec
TYPE_ID = '信息录入'
FIELDS = (FieldSpec('图像路径', '输入位置图像', 'path', '', required=True), FieldSpec('工作簿', '工作簿路径', 'path', '', required=True), FieldSpec('工作表', '工作表'), FieldSpec('单元格', '单元格', 'text', 'A1', required=True), FieldSpec('递增', '按循环次数递增行', 'bool', False), FieldSpec('模拟输入', '逐字符模拟输入', 'bool', False), FieldSpec('异常', '图像查找超时', 'text', '自动略过'), FieldSpec('空值处理', 'Excel空值处理', 'choice', '抛出异常', ('抛出异常', '自动跳过')))
