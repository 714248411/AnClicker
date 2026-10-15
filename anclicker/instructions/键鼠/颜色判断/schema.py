"""Instruction parameter schema."""
from __future__ import annotations
from anclicker.domain.fields import FieldSpec
TYPE_ID = '颜色判断'
FIELDS = (FieldSpec('坐标', '检测坐标 x,y', default='0,0', required=True), FieldSpec('颜色', '目标颜色', default='#FFFFFF', required=True), FieldSpec('容差', 'RGB 单通道容差', 'int', 0, minimum=0, maximum=255), FieldSpec('比较', '判断方式', 'choice', '相等', ('相等', '不相等')), FieldSpec('变量', '结果变量（可选）'))
