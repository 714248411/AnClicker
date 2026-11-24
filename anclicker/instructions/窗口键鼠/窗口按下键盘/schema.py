from dataclasses import replace
from anclicker.instructions.窗口键鼠.窗口键盘.schema import FIELDS as BASE_FIELDS
TYPE_ID = '窗口按下键盘'
OPERATIONS = ('组合键',)
FIELDS = tuple(replace(field, choices=OPERATIONS, default='组合键') if field.key == '操作' else field for field in BASE_FIELDS)
