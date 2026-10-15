"""Instruction parameter schema."""
from __future__ import annotations
from anclicker.domain.fields import FieldSpec
TYPE_ID = '条件判断'
FIELDS = (FieldSpec('条件', '判断条件', 'text', 'True', required=True),)
