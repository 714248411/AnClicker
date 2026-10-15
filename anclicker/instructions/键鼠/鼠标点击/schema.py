"""Instruction parameter schema."""
from __future__ import annotations
from anclicker.domain.fields import FieldSpec
TYPE_ID = '鼠标点击'
FIELDS = (FieldSpec('鼠标', '鼠标按键', 'choice', '左键', ('左键', '右键', '中键', '侧键1', '侧键2', '其他（录制）')), FieldSpec('次数', '点击次数', 'int', 1, minimum=1, maximum=9999), FieldSpec('间隔', '点击间隔（毫秒）', 'int', 100, minimum=0, maximum=3600000), FieldSpec('按压', '按压时长（毫秒）', 'int', 50, minimum=0, maximum=3600000), FieldSpec('辅助键', '辅助键'))
