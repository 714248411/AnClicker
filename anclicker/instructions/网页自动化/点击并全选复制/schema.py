"""Instruction parameter schema."""
from __future__ import annotations
from anclicker.domain.fields import FieldSpec
TYPE_ID = '点击并全选复制'
FIELDS = (FieldSpec('selector', '元素定位(点它并把它里面的内容全选复制)', 'text', '', choices=(), minimum=0), FieldSpec('anchor', '锚点元素(可选，多个用;分隔)', 'text', '', choices=(), minimum=0), FieldSpec('anchorRel', '目标相对锚点的方位', 'choice', '下方', choices=('下方', '上方', '右侧', '左侧', '内部', '相邻'), minimum=0), FieldSpec('clickType', '点击方式', 'choice', '单击', choices=('单击', '双击', '右键'), minimum=0), FieldSpec('by', '定位方式', 'choice', '智能匹配', choices=('CSS选择器', 'XPath', '文本内容', '智能匹配', '锚点定位'), minimum=0))
