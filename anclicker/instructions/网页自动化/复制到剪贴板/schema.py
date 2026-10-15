"""Instruction parameter schema."""
from __future__ import annotations
from anclicker.domain.fields import FieldSpec
TYPE_ID = '复制到剪贴板'
FIELDS = (FieldSpec('from', '复制什么', 'choice', '文本(下面填的内容)', choices=('文本(下面填的内容)', '网页里选中的内容', '元素里的文本'), minimum=0), FieldSpec('content', '要复制的文本(可用 ${变量})', 'text', '', choices=(), minimum=0), FieldSpec('selector', '元素定位(上面选「元素里的文本」时填)', 'text', '', choices=(), minimum=0), FieldSpec('by', '定位方式', 'choice', '智能匹配', choices=('CSS选择器', 'XPath', '文本内容', '智能匹配'), minimum=0))
