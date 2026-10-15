"""Instruction parameter schema."""
from __future__ import annotations
from anclicker.domain.fields import FieldSpec
TYPE_ID = '中键激活'
FIELDS = (FieldSpec('类型', '激活类型', 'choice', '模拟点击', ('模拟点击', '结束等待')), FieldSpec('次数', '次数', 'int', 1, minimum=1, maximum=9999))
