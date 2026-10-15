"""Instruction parameter schema."""
from __future__ import annotations
from anclicker.domain.fields import FieldSpec
TYPE_ID = '表格另存为'
FIELDS = (FieldSpec('naming', '命名方式', 'choice', '后缀递增', choices=('后缀递增', '加前缀', '覆盖'), minimum=0), FieldSpec('prefix', '前缀(选「加前缀」时用)', 'text', '', choices=(), minimum=0), FieldSpec('startIndex', '后缀从几开始(默认1)', 'int', 1, choices=(), minimum=1))
