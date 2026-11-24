from dataclasses import replace
from anclicker.instructions.窗口键鼠.窗口键鼠.schema import FIELDS as BASE_FIELDS
TYPE_ID = '窗口OCR点击'
OPERATIONS = ('左键单击',)
FIELDS = tuple(replace(field, choices=OPERATIONS, default='左键单击') if field.key == '操作' else field for field in BASE_FIELDS)

from anclicker.domain.fields import FieldSpec
EXTRA_FIELDS = (FieldSpec('目标文字','目标文字（留空匹配全部）','text',''), FieldSpec('引擎','识别引擎','choice','RapidOCR',('RapidOCR','微信OCR')), FieldSpec('匹配方式','匹配方式','choice','包含',('精准','包含','模糊')), FieldSpec('第几个','第几个结果','int',1,minimum=1,maximum=10000), FieldSpec('置信度','最低置信度','float',0.5,minimum=0,maximum=1), FieldSpec('变量','结果变量','text','OCR坐标'), FieldSpec('识别超时','识别超时（秒）','float',30,minimum=1,maximum=300), FieldSpec('未找到','未找到时','choice','报错',('报错','返回空值')),)
FIELDS += EXTRA_FIELDS
