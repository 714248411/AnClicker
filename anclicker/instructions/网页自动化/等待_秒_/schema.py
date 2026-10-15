"""Instruction parameter schema."""
from __future__ import annotations
from anclicker.domain.fields import FieldSpec
TYPE_ID = '等待（秒）'
FIELDS = (FieldSpec('seconds', '等待时间(秒)', 'float', 1, choices=(), minimum=0),)
