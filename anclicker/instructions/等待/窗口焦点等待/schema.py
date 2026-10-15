"""Instruction parameter schema."""
from __future__ import annotations
from anclicker.domain.fields import FieldSpec
TYPE_ID = '窗口焦点等待'
FIELDS = (FieldSpec('标题包含', '窗口标题包含', 'text', '', required=True), FieldSpec('检测频率', '检测频率', 'float', 0.2, minimum=0.01, maximum=60), FieldSpec('等待时间', '超时时间', 'float', 30, minimum=0, maximum=86400), FieldSpec('等待类型', '等待类型', 'choice', '获得焦点', ('获得焦点', '失去焦点')))
