"""Instruction parameter schema."""
from __future__ import annotations
from anclicker.domain.fields import FieldSpec
TYPE_ID = '提示音'
FIELDS = (FieldSpec('类型', '提示音类型', 'choice', '系统提示音', ('系统提示音', '蜂鸣', 'TTS')), FieldSpec('频率', '蜂鸣频率', 'int', 800, minimum=37, maximum=32767), FieldSpec('持续', '持续毫秒', 'int', 300, minimum=1, maximum=60000), FieldSpec('次数', '播放次数', 'int', 1, minimum=1, maximum=999), FieldSpec('间隔', '播放间隔', 'float', 0.1, minimum=0, maximum=60), FieldSpec('提示类型', '系统提示类型', 'choice', '信息', ('警告', '错误', '询问', '信息', '系统启动', '系统关闭')), FieldSpec('内容', 'TTS内容', 'multiline', ''), FieldSpec('语速', 'TTS语速', 'int', 200, minimum=50, maximum=500))
