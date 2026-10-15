"""Instruction parameter schema."""
from __future__ import annotations
from anclicker.domain.fields import FieldSpec
TYPE_ID = '表格复制粘贴'
FIELDS = (FieldSpec('fromBook', '源表格(留空=当前)', 'text', '', choices=(), minimum=0), FieldSpec('fromSheet', '源工作表', 'text', 'Sheet1', choices=(), minimum=0), FieldSpec('fromRange', '源区域(如A1:C5)', 'text', 'A1:C5', choices=(), minimum=0), FieldSpec('toBook', '目标表格(留空=当前)', 'text', '', choices=(), minimum=0), FieldSpec('toSheet', '目标工作表', 'text', 'Sheet1', choices=(), minimum=0), FieldSpec('toRange', '目标起始单元格(如A1)', 'text', 'A1', choices=(), minimum=0), FieldSpec('mode', '粘贴方式', 'choice', '全部粘贴', choices=('全部粘贴', '只粘贴值', '只粘贴公式', '只粘贴格式', '保留公式', '值与数字格式', '公式与数字格式', '不覆盖原有内容'), minimum=0))
