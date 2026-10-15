"""Instruction parameter schema."""
from __future__ import annotations
from anclicker.domain.fields import FieldSpec
TYPE_ID = '移动鼠标'
FIELDS = (FieldSpec('类型', '移动类型', 'choice', '直线移动', ('直线移动', '随机移动', '指定坐标', '变量坐标')), FieldSpec('方向', '方向', 'choice', '→', ('↑', '↓', '←', '→')), FieldSpec('距离', '距离', 'int', 100, minimum=0, maximum=100000), FieldSpec('随机', '随机方式', 'choice', '类型1', ('类型1', '类型2')), FieldSpec('坐标', '目标坐标 x,y', 'text', '0,0'), FieldSpec('持续', '持续秒数', 'float', 0.2, minimum=0, maximum=3600), FieldSpec('变量', '坐标变量'))
