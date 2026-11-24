from anclicker.domain.fields import FieldSpec
TYPE_ID='截图OCR核验'
FIELDS=(FieldSpec('预期文字','必须出现的文字（多项用 | 分隔）','text','',required=True), FieldSpec('窗口标题','目标窗口完整标题'), FieldSpec('区域','截图区域 x,y,w,h（与窗口标题二选一）'), FieldSpec('置信度','最低 OCR 置信度','float',0.7,minimum=0,maximum=1), FieldSpec('识别超时','单次识别超时（秒）','int',20,minimum=1,maximum=120), FieldSpec('未通过时报错','未通过时停止流程','bool',True),)
