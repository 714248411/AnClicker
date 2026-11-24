from anclicker.domain.fields import FieldSpec
TYPE_ID = '提取转Excel'
FIELDS = (
    FieldSpec('保存路径', '保存为', 'path', required=True),
    FieldSpec('文件已存在', '文件已存在', 'choice', '自动更名', ('自动更名', '覆盖', '报错')),
)
