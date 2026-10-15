"""Instruction parameter schema."""
from __future__ import annotations
from anclicker.domain.fields import FieldSpec
TYPE_ID = '等待元素出现'
FIELDS = (FieldSpec('selector', '元素定位', 'text', '', choices=(), minimum=0), FieldSpec('anchor', '锚点元素(可选，多个用;分隔)', 'text', '', choices=(), minimum=0), FieldSpec('anchorRel', '目标相对锚点的方位', 'choice', '下方', choices=('下方', '上方', '右侧', '左侧', '内部', '相邻'), minimum=0), FieldSpec('timeout', '超时(秒)', 'float', 10, choices=(), minimum=0), FieldSpec('fallbackToXY', '超时还没出现怎么办', 'choice', '只报错', choices=('只报错', '点击坐标'), minimum=0), FieldSpec('xyPoints', '兜底点击坐标(没出现时点这里，最多9个点用;分隔)', 'text', '', choices=(), minimum=0), FieldSpec('xyInterval', '兜底点击的间隔(秒)', 'float', 1, choices=(), minimum=0), FieldSpec('by', '定位方式', 'choice', '智能匹配', choices=('CSS选择器', 'XPath', '文本内容', '智能匹配', '锚点定位'), minimum=0))
