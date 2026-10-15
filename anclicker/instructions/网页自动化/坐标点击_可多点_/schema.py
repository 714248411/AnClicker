"""Instruction parameter schema."""
from __future__ import annotations
from anclicker.domain.fields import FieldSpec
TYPE_ID = '坐标点击（可多点）'
FIELDS = (FieldSpec('points', '点击坐标（按顺序执行，用分号分隔）', 'text', '', choices=(), minimum=0), FieldSpec('interval', '每个点之间间隔(秒)', 'float', 1, choices=(), minimum=0), FieldSpec('clickType', '点击方式', 'choice', '单击', choices=('单击', '双击', '右键'), minimum=0), FieldSpec('x', 'X坐标(只在单点、且上面没填时用)', 'float', 0, choices=(), minimum=0), FieldSpec('y', 'Y坐标(只在单点、且上面没填时用)', 'float', 0, choices=(), minimum=0), FieldSpec('randomOffset', '随机偏移', 'choice', '关闭', choices=('关闭', '启用')), FieldSpec('offsetX', '水平偏移范围 ± 像素', 'int', 0, minimum=0, maximum=1000), FieldSpec('offsetY', '垂直偏移范围 ± 像素', 'int', 0, minimum=0, maximum=1000))
