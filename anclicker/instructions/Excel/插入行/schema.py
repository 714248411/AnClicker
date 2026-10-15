"""Instruction parameter schema."""
from __future__ import annotations
from anclicker.domain.fields import FieldSpec
TYPE_ID = '插入行'
FIELDS = (FieldSpec('row', '在第几行前插入', 'int', 1, choices=(), minimum=1), FieldSpec('count', '插入行数', 'int', 1, choices=(), minimum=1))
