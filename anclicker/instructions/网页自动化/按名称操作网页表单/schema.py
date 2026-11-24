from anclicker.domain.fields import FieldSpec
TYPE_ID = '按名称操作网页表单'
FIELDS = (FieldSpec('action', '操作', 'choice', '填入', choices=('填入', '清空', '选择', '勾选', '取消勾选'), required=False, minimum=0, maximum=60),
FieldSpec('label', '页面上的字段名称', 'text', '', choices=(), required=True, minimum=0, maximum=60),
FieldSpec('value', '填写内容或选项文字', 'text', '', choices=(), required=False, minimum=0, maximum=60),)
