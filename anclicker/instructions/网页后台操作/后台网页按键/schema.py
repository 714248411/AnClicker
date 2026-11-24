from dataclasses import replace
from anclicker.domain.fields import FieldSpec
from anclicker.instructions.网页自动化.按键.schema import FIELDS as BASE_FIELDS
FIELDS = tuple(
    replace(field, label='自定义按键/连续字符（如 aaaaa、F5、Ctrl+Shift+A）') if field.key == 'customKey' else replace(field, maximum=20) if field.key == 'times' else field
    for field in BASE_FIELDS
) + (FieldSpec('interval', '按键间隔（秒）', 'float', 0.1, minimum=0, maximum=3600),)
