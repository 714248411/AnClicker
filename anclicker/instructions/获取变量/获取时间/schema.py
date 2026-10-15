"""Instruction parameter schema."""
from __future__ import annotations
from anclicker.domain.fields import FieldSpec
TYPE_ID = '获取时间'
FIELDS = (FieldSpec('变量', '变量名称', 'text', '当前时间', required=True), FieldSpec('时间格式', '时间格式', 'choice', '年-月-日 小时:分钟:秒', ('年-月-日 小时:分钟:秒', '年/月/日 小时:分钟:秒', '月/日/年 小时:分钟:秒', '日-月-年 小时:分钟:秒', '年-月-日', '月/日/年', '日-月-年', '月/年', '时间戳'), required=True))
