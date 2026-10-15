"""Instruction parameter schema."""
from __future__ import annotations
from anclicker.domain.fields import FieldSpec
TYPE_ID = 'OCR识别'
FIELDS = (FieldSpec('区域', '识别区域 x,y,w,h', 'text', '', required=True), FieldSpec('变量', '变量名称', 'text', 'OCR结果', required=True))
