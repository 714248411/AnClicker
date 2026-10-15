"""Instruction parameter schema."""
from __future__ import annotations
from anclicker.domain.fields import FieldSpec
TYPE_ID = '时间等待'
FIELDS = (FieldSpec('类型', '等待类型', 'choice', '时间等待', ('时间等待', '随机等待', '定时等待')), FieldSpec('时长', '时长', 'float', 1, minimum=0, maximum=86400), FieldSpec('单位', '单位', 'choice', '秒', ('毫秒', '秒', '分钟')), FieldSpec('最小', '随机最小秒数', 'float', 1, minimum=0, maximum=86400), FieldSpec('最小单位', '随机最小值单位', 'choice', '秒', ('毫秒', '秒', '分钟')), FieldSpec('最大', '随机最大秒数', 'float', 3, minimum=0, maximum=86400), FieldSpec('最大单位', '随机最大值单位', 'choice', '秒', ('毫秒', '秒', '分钟')), FieldSpec('时间', '目标时间 HH:MM:SS'), FieldSpec('检测频率', '检测频率', 'float', 0.2, minimum=0.01, maximum=60))
