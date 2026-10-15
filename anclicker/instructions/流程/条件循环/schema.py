"""Instruction parameter schema."""
from __future__ import annotations
from anclicker.domain.fields import FieldSpec
TYPE_ID = '条件循环'
FIELDS = (FieldSpec('方式', '循环方式', 'choice', '条件', ('次数', '条件')), FieldSpec('条件', '判断条件', 'text', 'True', required=True), FieldSpec('次数', '循环次数', 'int', 3))
