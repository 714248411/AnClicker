"""Instruction parameter schema."""
from __future__ import annotations
from anclicker.domain.fields import FieldSpec
TYPE_ID = '粘贴到单元格'
FIELDS = (FieldSpec('toPath', '写到哪个表格(可拖文件进来，留空=新建到桌面)', 'text', '', choices=(), minimum=0), FieldSpec('toSheet', '工作表名(留空=第一个表)', 'text', '', choices=(), minimum=0), FieldSpec('toCell', '从哪个单元格开始粘贴(如 A1、B2)', 'text', 'A1', choices=(), minimum=0), FieldSpec('save', '保存方式', 'choice', '保存', choices=('保存', '另存为'), minimum=0))
