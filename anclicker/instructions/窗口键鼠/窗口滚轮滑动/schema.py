from dataclasses import replace
from anclicker.instructions.窗口键鼠.窗口键鼠.schema import FIELDS as BASE_FIELDS
TYPE_ID = '窗口滚轮滑动'
OPERATIONS = ('滚轮滑动',)
FIELDS = tuple(replace(field, choices=OPERATIONS, default='滚轮滑动') if field.key == '操作' else field for field in BASE_FIELDS)
