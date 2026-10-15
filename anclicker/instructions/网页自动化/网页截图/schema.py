"""Instruction parameter schema."""
from __future__ import annotations
from anclicker.domain.fields import FieldSpec
TYPE_ID = '网页截图'
FIELDS = (FieldSpec('selector', '元素定位(可选)', 'text', '', choices=(), minimum=0), FieldSpec('path', '保存路径', 'text', '', choices=(), minimum=0))
