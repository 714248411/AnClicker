"""Instruction parameter schema."""
from __future__ import annotations
from anclicker.domain.fields import FieldSpec
TYPE_ID = '提示窗口'
FIELDS = (FieldSpec('标题', '窗口标题', 'text', '提示'), FieldSpec('内容', '提示内容', 'multiline', ''), FieldSpec('图标', '图标', 'choice', '信息', ('无', '信息', '警告', '错误', '询问')))
