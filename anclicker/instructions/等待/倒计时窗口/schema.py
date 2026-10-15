"""Instruction parameter schema."""
from __future__ import annotations
from anclicker.domain.fields import FieldSpec
TYPE_ID = '倒计时窗口'
FIELDS = (FieldSpec('标题', '窗口标题', 'text', '倒计时'), FieldSpec('内容', '提示内容', 'multiline', '请稍候'), FieldSpec('秒数', '倒计时秒数', 'int', 5, minimum=0, maximum=86400))
