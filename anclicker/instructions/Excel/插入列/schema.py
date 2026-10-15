"""Instruction parameter schema."""
from __future__ import annotations
from anclicker.domain.fields import FieldSpec
TYPE_ID = '插入列'
FIELDS = (FieldSpec('col', '在第几列前插入', 'int', 1, choices=(), minimum=1), FieldSpec('count', '插入列数', 'int', 1, choices=(), minimum=1))
