"""Instruction parameter schema."""
from __future__ import annotations
from anclicker.domain.fields import FieldSpec
TYPE_ID = '悬停后点击'
FIELDS = (FieldSpec('悬停位置', '悬停位置 x,y', 'text', '0,0', required=True), FieldSpec('点击位置', '点击位置 x,y', 'text', '0,0', required=True), FieldSpec('停留时间', '悬停等待（秒）', 'float', 1.5, minimum=0, maximum=3600), FieldSpec('移动秒数', '连续移动（秒）', 'float', 1.0, minimum=0, maximum=3600), FieldSpec('点击前停留', '点击前等待（秒）', 'float', 0.3, minimum=0, maximum=3600), FieldSpec('动作', '点击动作', 'choice', '左键单击', choices=('左键单击', '左键双击', '右键单击', '中键单击')))
