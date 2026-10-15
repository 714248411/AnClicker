"""Instruction parameter schema."""
from __future__ import annotations
from anclicker.domain.fields import FieldSpec
TYPE_ID = '终止流程'
FIELDS = (FieldSpec('终止类型', '终止类型', 'choice', '终止所有任务', ('终止所有任务',)),)
