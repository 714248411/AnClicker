from anclicker.domain.fields import FieldSpec
TYPE_ID = '折叠步骤'
FIELDS = (
    FieldSpec('按条数', '折叠下方条数', 'bool', True),
    FieldSpec('下方条数', '下方条数', 'int', 1, minimum=1),
    FieldSpec('按范围', '按步骤范围', 'bool', False),
    FieldSpec('终止步骤', '从下一步至第几步', 'int', 9, minimum=1),
    FieldSpec('动态范围', '动态折叠范围', 'bool', True),
    FieldSpec('整体锁定', '整体移动锁定', 'bool', False),
    FieldSpec('已折叠', '折叠状态', 'bool', True),
)
