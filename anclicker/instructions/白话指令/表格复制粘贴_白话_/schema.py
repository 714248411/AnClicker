"""Instruction parameter schema."""
from __future__ import annotations
from anclicker.domain.fields import FieldSpec
TYPE_ID = '表格复制粘贴（白话）'
FIELDS = (FieldSpec('fromPath', '① 源表格路径(可把Excel文件拖进来)', 'text', '', choices=(), minimum=0), FieldSpec('fromRanges', '② 复制哪几列/区域(如 A1-A9,B2-B4；留空=整个表格)', 'text', '', choices=(), minimum=0), FieldSpec('fromSheet', '③ 源工作表名(留空=第一个表)', 'text', '', choices=(), minimum=0), FieldSpec('toPath', '④ 目标表格路径(可拖文件进来，留空=新建到桌面)', 'text', '', choices=(), minimum=0), FieldSpec('toSheet', '⑤ 目标工作表名(留空=第一个表)', 'text', '', choices=(), minimum=0), FieldSpec('toCell', '⑥ 从哪个单元格开始粘贴(如 B1、D2)', 'text', 'A1', choices=(), minimum=0), FieldSpec('mode', '⑦ 粘贴方式', 'choice', '只粘贴文本', choices=('只粘贴文本', '全部粘贴', '只粘贴值', '只粘贴公式', '只粘贴格式', '保留公式', '值与数字格式', '公式与数字格式', '不覆盖原有内容'), minimum=0), FieldSpec('save', '⑧ 粘贴后是否保存表格', 'choice', '保存', choices=('保存', '不保存'), minimum=0))
