"""Instruction parameter schema."""
from __future__ import annotations
from anclicker.domain.fields import FieldSpec
TYPE_ID = '窗口控制'
FIELDS = (FieldSpec('标题包含', '窗口标题包含', 'text', '', required=True), FieldSpec('操作', '窗口操作', 'choice', '激活', ('激活', '最小化', '最大化', '还原', '关闭')), FieldSpec('报错', '未找到时报错', 'bool', True))
