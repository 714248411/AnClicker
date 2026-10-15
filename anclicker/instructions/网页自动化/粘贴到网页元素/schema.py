"""Instruction parameter schema."""
from __future__ import annotations
from anclicker.domain.fields import FieldSpec
TYPE_ID = '粘贴到网页元素'
FIELDS = (FieldSpec('selector', '元素定位(要粘贴到哪个元素)', 'text', '', choices=(), minimum=0), FieldSpec('anchor', '锚点元素(可选，多个用;分隔)', 'text', '', choices=(), minimum=0), FieldSpec('anchorRel', '目标相对锚点的方位', 'choice', '下方', choices=('下方', '上方', '右侧', '左侧', '内部', '相邻'), minimum=0), FieldSpec('mode', '粘贴方式', 'choice', '真实粘贴(Ctrl+V)', choices=('真实粘贴(Ctrl+V)', '直接把内容写进去'), minimum=0), FieldSpec('by', '定位方式', 'choice', '智能匹配', choices=('CSS选择器', 'XPath', '文本内容', '智能匹配', '锚点定位'), minimum=0))
