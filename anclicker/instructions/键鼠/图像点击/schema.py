"""Instruction parameter schema."""
from __future__ import annotations
from anclicker.domain.fields import FieldSpec
TYPE_ID = '图像点击'
FIELDS = (FieldSpec('图像路径', '图像路径', 'path', '', required=True), FieldSpec('动作', '鼠标动作', 'choice', '左键单击', ('左键单击', '左键双击', '左键三击', '右键单击', '右键双击', '仅移动鼠标', '无操作')), FieldSpec('异常', '未找到图像', 'text', '自动略过'), FieldSpec('区域', '识别区域 x,y,w,h'), FieldSpec('灰度', '灰度识别', 'bool', False), FieldSpec('精度', '识别精度', 'float', 0.8, minimum=0.01, maximum=1.0), FieldSpec('点击位置', '点击偏移 x,y', 'text', '(0,0)'))
