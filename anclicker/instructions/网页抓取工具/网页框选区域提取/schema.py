from anclicker.domain.fields import FieldSpec
TYPE_ID='网页框选区域提取'
FIELDS=(FieldSpec('区域','网页框选区域',required=True),FieldSpec('最大字符数','最大字符数','int',20000,minimum=500,maximum=200000))
