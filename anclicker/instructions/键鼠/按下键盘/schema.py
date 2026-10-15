"""Instruction parameter schema."""
from __future__ import annotations
from anclicker.domain.fields import FieldSpec
TYPE_ID = '按下键盘'
FIELDS = (FieldSpec('按键', '按键（用 + 组合）', 'text', 'enter', required=True), FieldSpec('按压时长', '按压时长（毫秒）', 'int', 50, minimum=0, maximum=3600000))
