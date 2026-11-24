from dataclasses import replace
from anclicker.instructions.窗口键鼠.窗口键鼠.schema import FIELDS as BASE_FIELDS
TYPE_ID = '窗口鼠标拖拽'
OPERATIONS = ('鼠标拖拽',)
FIELDS = tuple(replace(field, choices=OPERATIONS, default='鼠标拖拽') if field.key == '操作' else field for field in BASE_FIELDS)
