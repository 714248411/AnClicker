"""Instruction parameter schema."""
from __future__ import annotations
from anclicker.domain.fields import FieldSpec
TYPE_ID = '多图点击'
FIELDS = (FieldSpec('图像路径', '图像路径（每行一个）', 'multiline', '', required=True), FieldSpec('动作', '鼠标动作', 'choice', '左键单击', ('左键单击', '左键双击', '右键单击', '右键双击', '仅移动鼠标')), FieldSpec('异常', '全部未找到', 'text', '自动略过'), FieldSpec('区域', '识别区域 x,y,w,h'), FieldSpec('灰度', '灰度识别', 'bool', False), FieldSpec('精度', '识别精度', 'float', 0.8, minimum=0.01, maximum=1.0))
