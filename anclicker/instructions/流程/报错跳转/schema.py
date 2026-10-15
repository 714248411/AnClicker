"""Instruction parameter schema."""
from __future__ import annotations
from anclicker.domain.fields import FieldSpec
from anclicker.domain.flow_jumps import TARGET_MODES
TYPE_ID = '报错跳转'
FIELDS = (FieldSpec('跳转方式', '跳转方式', 'choice', '连线节点', TARGET_MODES), FieldSpec('目标行', '目标行（表格序号，从 1 开始）', 'int', 1), FieldSpec('项目路径', '目标项目文件', 'text', ''))
