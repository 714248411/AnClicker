"""Instruction parameter schema."""
from __future__ import annotations
from anclicker.domain.fields import FieldSpec
TYPE_ID = '坐标点击'
FIELDS = (FieldSpec('动作', '鼠标动作', 'choice', '左键单击', ('左键单击', '左键双击', '右键单击', '右键双击', '左键（自定义次数）', '仅移动鼠标')), FieldSpec('坐标', '坐标 x-y', 'text', '0-0', required=True), FieldSpec('自定义次数', '点击次数', 'int', 1, minimum=1, maximum=9999))
