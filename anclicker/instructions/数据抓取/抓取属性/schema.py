"""Instruction parameter schema."""
from __future__ import annotations
from anclicker.domain.fields import FieldSpec
TYPE_ID = '抓取属性'
FIELDS = (FieldSpec('selector', '元素定位', 'text', '', choices=(), minimum=0), FieldSpec('attr', '属性名(如href)', 'text', 'href', choices=(), minimum=0), FieldSpec('varName', '保存到变量', 'text', '抓取结果', choices=(), minimum=0), FieldSpec('by', '定位方式', 'choice', '智能匹配', choices=('CSS选择器', 'XPath', '智能匹配'), minimum=0), FieldSpec('all', '抓取数量', 'choice', '全部匹配', choices=('单个', '全部匹配'), minimum=0))
