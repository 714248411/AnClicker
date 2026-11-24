from anclicker.instructions.窗口键鼠.窗口键鼠.schema import FIELDS as ALL_FIELDS, OPERATIONS as ALL_OPERATIONS
TYPE_ID = '窗口键盘'
OPERATIONS = ('组合键', '输入内容')
from dataclasses import replace
FIELDS = tuple(replace(field, choices=OPERATIONS, default=OPERATIONS[0]) if field.key == '操作' else field
               for field in ALL_FIELDS if field.key in ('窗口', '模式', '操作', '按键'))

from anclicker.domain.fields import FieldSpec
FIELDS += (FieldSpec('内容', '输入内容', 'multiline', ''),)
