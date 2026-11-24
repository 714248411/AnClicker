from dataclasses import replace
from anclicker.instructions.窗口键鼠.窗口键鼠.schema import FIELDS as BASE_FIELDS
TYPE_ID = '窗口悬停后点击'
OPERATIONS = ('左键单击',)
FIELDS = tuple(replace(field, choices=OPERATIONS, default='左键单击') if field.key == '操作' else field for field in BASE_FIELDS)

from anclicker.domain.fields import FieldSpec
EXTRA_FIELDS = (FieldSpec('停留时间','悬停时间（秒）','float',1.5,minimum=0,maximum=3600),)
FIELDS += EXTRA_FIELDS
