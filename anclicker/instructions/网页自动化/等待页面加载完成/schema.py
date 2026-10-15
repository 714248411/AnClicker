"""Instruction parameter schema."""
from __future__ import annotations
from anclicker.domain.fields import FieldSpec
TYPE_ID = '等待页面加载完成'
FIELDS = (FieldSpec('timeout', '最长等多久(秒)', 'float', 20, choices=(), minimum=0),)
