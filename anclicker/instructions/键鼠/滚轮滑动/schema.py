"""Instruction parameter schema."""
from __future__ import annotations
from anclicker.domain.fields import FieldSpec
TYPE_ID = '滚轮滑动'
FIELDS = (FieldSpec('类型', '滑动类型', 'choice', '滚轮滑动', ('滚轮滑动', '随机滚轮滑动')), FieldSpec('方向', '方向', 'choice', '向下', ('向上', '向下')), FieldSpec('距离', '距离', 'int', 5, minimum=1, maximum=100000), FieldSpec('最小距离', '随机最小距离', 'int', 1, minimum=1, maximum=100000), FieldSpec('最大距离', '随机最大距离', 'int', 10, minimum=1, maximum=100000))
