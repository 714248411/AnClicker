"""Instruction parameter schema."""
from __future__ import annotations
from anclicker.domain.fields import FieldSpec
TYPE_ID = '抓取列表'
FIELDS = (FieldSpec('selector', '列表项定位', 'text', '', choices=(), minimum=0), FieldSpec('fields', '字段(定位:字段名,逗号分隔)', 'text', '', choices=(), minimum=0), FieldSpec('varName', '保存到变量(二维数组)', 'text', '抓取列表', choices=(), minimum=0), FieldSpec('by', '定位方式', 'choice', '智能匹配', choices=('CSS选择器', 'XPath', '智能匹配'), minimum=0))
