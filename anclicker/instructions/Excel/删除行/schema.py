"""Instruction parameter schema."""
from __future__ import annotations
from anclicker.domain.fields import FieldSpec
TYPE_ID = '删除行'
FIELDS = (FieldSpec('row', '起始行', 'int', 1, choices=(), minimum=1), FieldSpec('count', '删除行数', 'int', 1, choices=(), minimum=1))
