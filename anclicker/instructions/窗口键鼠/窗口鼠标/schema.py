from anclicker.instructions.窗口键鼠.窗口键鼠.schema import FIELDS as ALL_FIELDS, OPERATIONS as ALL_OPERATIONS
TYPE_ID = '窗口鼠标'
OPERATIONS = tuple(op for op in ALL_OPERATIONS if op != '组合键')
from dataclasses import replace
FIELDS = tuple(replace(field, choices=OPERATIONS, default=OPERATIONS[0]) if field.key == '操作' else field
               for field in ALL_FIELDS if field.key != '按键')
