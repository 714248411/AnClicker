"""Instruction parameter schema."""
from __future__ import annotations
from anclicker.domain.fields import FieldSpec
TYPE_ID = '拾取元素'
FIELDS = (FieldSpec('hint', '说明', 'text', '在浏览器里点击目标元素', choices=(), minimum=0),)
