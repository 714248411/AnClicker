"""Instruction parameter schema."""
from __future__ import annotations
from anclicker.domain.fields import FieldSpec
TYPE_ID = '移动鼠标'
FIELDS = (FieldSpec('类型', '移动类型', 'choice', '模拟人1（WindMouse）', ('直线移动', '随机移动', '指定坐标', '变量坐标', '模拟人1（WindMouse）', '模拟人2（BezMouse）')), FieldSpec('方向', '方向', 'choice', '无', ('↑', '↓', '←', '→', '无')), FieldSpec('距离', '距离', 'int', 100, minimum=0, maximum=100000), FieldSpec('随机', '随机方式', 'choice', '类型1', ('类型1', '类型2')), FieldSpec('坐标', '移动目标', 'text', '0,0'), FieldSpec('持续', '移动时间（秒）', 'text', '0.5-1.5'), FieldSpec('变量', '坐标变量'))
