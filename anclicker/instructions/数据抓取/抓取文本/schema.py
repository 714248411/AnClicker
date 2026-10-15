"""Instruction parameter schema."""
from __future__ import annotations
from anclicker.domain.fields import FieldSpec
TYPE_ID = '抓取文本'
FIELDS = (FieldSpec('selector', '元素定位', 'text', '', choices=(), minimum=0), FieldSpec('varName', '保存到变量', 'text', '抓取结果', choices=(), minimum=0), FieldSpec('by', '定位方式', 'choice', '智能匹配', choices=('CSS选择器', 'XPath', '文本内容', '智能匹配'), minimum=0), FieldSpec('all', '抓取数量', 'choice', '单个', choices=('单个', '全部匹配'), minimum=0))
