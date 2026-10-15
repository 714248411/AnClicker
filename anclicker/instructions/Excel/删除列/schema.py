"""Instruction parameter schema."""
from __future__ import annotations
from anclicker.domain.fields import FieldSpec
TYPE_ID = '删除列'
FIELDS = (FieldSpec('col', '起始列', 'int', 1, choices=(), minimum=1), FieldSpec('count', '删除列数', 'int', 1, choices=(), minimum=1))
