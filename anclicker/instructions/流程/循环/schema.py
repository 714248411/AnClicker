"""Instruction parameter schema."""
from __future__ import annotations
from anclicker.domain.fields import FieldSpec
TYPE_ID = '循环'
FIELDS = (FieldSpec('方式', '循环方式', 'choice', '次数', ('次数', '条件')), FieldSpec('条件', '条件表达式', 'text', 'True'), FieldSpec('次数', '循环次数', 'int', 3))
