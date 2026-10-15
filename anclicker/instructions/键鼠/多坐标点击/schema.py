"""Instruction parameter schema."""
from __future__ import annotations
from anclicker.domain.fields import FieldSpec
TYPE_ID = '多坐标点击'
FIELDS = (FieldSpec('坐标列表', '点击坐标', 'text', '', required=True), FieldSpec('动作', '点击方式', 'choice', '左键单击', ('左键单击', '左键双击', '右键单击', '中键单击')), FieldSpec('间隔', '各点间隔（秒）', 'float', 1, minimum=0, maximum=3600), FieldSpec('随机偏移', '随机偏移', 'choice', '关闭', ('关闭', '启用')), FieldSpec('水平偏移', '水平随机范围', 'int', 0, minimum=0, maximum=1000), FieldSpec('垂直偏移', '垂直随机范围', 'int', 0, minimum=0, maximum=1000))
