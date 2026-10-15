"""Instruction parameter schema."""
from __future__ import annotations
from anclicker.domain.fields import FieldSpec
TYPE_ID = '按键等待'
FIELDS = (FieldSpec('按键', '等待按键', 'text', 'enter', required=True), FieldSpec('等待类型', '等待类型', 'choice', '按键等待', ('按键等待',)))
