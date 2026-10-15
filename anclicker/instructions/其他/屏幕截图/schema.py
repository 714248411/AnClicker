"""Instruction parameter schema."""
from __future__ import annotations
from anclicker.domain.fields import FieldSpec
TYPE_ID = '屏幕截图'
FIELDS = (FieldSpec('截图类型', '截图类型', 'choice', '全屏截图', ('全屏截图', '区域截图')), FieldSpec('区域', '截图区域 x,y,w,h'), FieldSpec('保存路径', '保存路径'), FieldSpec('截图后', '截图后操作', 'choice', '保存到路径', ('保存到路径', '写入剪切板')))
