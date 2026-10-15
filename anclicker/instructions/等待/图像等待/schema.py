"""Instruction parameter schema."""
from __future__ import annotations
from anclicker.domain.fields import FieldSpec
TYPE_ID = '图像等待'
FIELDS = (FieldSpec('图像路径', '图像路径', 'path', '', required=True), FieldSpec('等待类型', '等待类型', 'choice', '等待出现', ('等待出现', '等待消失')), FieldSpec('超时时间', '超时秒数（0 不限）', 'float', 10, minimum=0, maximum=86400), FieldSpec('区域', '识别区域 x,y,w,h'), FieldSpec('精度', '识别精度', 'float', 0.8, minimum=0.01, maximum=1.0))
