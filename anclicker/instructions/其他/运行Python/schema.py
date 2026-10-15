"""Instruction parameter schema."""
from __future__ import annotations
from anclicker.domain.fields import FieldSpec
TYPE_ID = '运行Python'
FIELDS = (FieldSpec('代码', 'Python代码', 'multiline', '', required=True), FieldSpec('返回值', '结果变量名', 'text', 'result'), FieldSpec('变量', '写入变量池', 'text', 'Python返回值'))
