"""提示窗口参数。变量可选，旧指令仍只显示提示内容。"""
from anclicker.domain.fields import FieldSpec
TYPE_ID = '提示窗口'
FIELDS = (
    FieldSpec('标题', '窗口标题', 'text', '提示'),
    FieldSpec('内容', '提示内容', 'multiline', ''),
    FieldSpec('图标', '图标', 'choice', '信息', ('无', '信息', '警告', '错误', '询问')),
    FieldSpec('变量', '附加变量（可选）', 'text', ''),
    FieldSpec('显示顺序', '显示顺序', 'choice', '提示内容在前', ('提示内容在前', '变量值在前')),
)
