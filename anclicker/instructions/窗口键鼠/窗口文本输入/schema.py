from dataclasses import replace
from anclicker.instructions.窗口键鼠.窗口键盘.schema import FIELDS as BASE_FIELDS
TYPE_ID = '窗口文本输入'
OPERATIONS = ('输入内容',)
FIELDS = tuple(replace(field, choices=OPERATIONS, default='输入内容') if field.key == '操作' else field for field in BASE_FIELDS)

from anclicker.domain.fields import FieldSpec
FIELDS += (FieldSpec('X','输入位置 X','int',0,minimum=0), FieldSpec('Y','输入位置 Y','int',0,minimum=0))
