"""Instruction parameter schema."""
from __future__ import annotations
from anclicker.domain.fields import FieldSpec
TYPE_ID = '后台字库管理'
FIELDS = (FieldSpec(key='接口', label='操作', kind='choice', default='SetPath', choices=('SetPath', '加载字库 · SetDict', '切换字库 · UseDict', 'GetNowDict', '添加字库文字 · AddDict', '清空字库 · ClearDict', 'GetDictCount', 'GetDictInfo', 'GetDict', 'SaveDict', '设置字库密码 · SetDictPwd', 'SetExportDict', 'EncodeFile', 'DecodeFile'), required=False, minimum=-1000000, maximum=1000000), FieldSpec(key='参数', label='接口参数', kind='multiline', default='{}', choices=(), required=False, minimum=-1000000, maximum=1000000), FieldSpec(key='变量', label='结果变量（可选）', kind='text', default='', choices=(), required=False, minimum=-1000000, maximum=1000000))
