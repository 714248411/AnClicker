"""Instruction parameter schema."""
from __future__ import annotations
from anclicker.execution.instruction_helpers.mouse_trajectory import TRAJECTORIES
from anclicker.domain.fields import FieldSpec
TYPE_ID = '鼠标拖拽'
FIELDS = (FieldSpec('开始位置', '开始位置 x,y', 'text', '0,0', required=True), FieldSpec('结束位置', '结束位置 x,y', 'text', '0,0', required=True), FieldSpec('开始随机', '开始位置随机偏移', 'bool', False), FieldSpec('结束随机', '结束位置随机偏移', 'bool', False), FieldSpec('移动速度', '移动秒数', 'float', 0.5, minimum=0, maximum=3600), FieldSpec('移动轨迹', '移动轨迹', 'choice', '直线', choices=TRAJECTORIES))
