"""Instruction parameter schema."""
from __future__ import annotations
from anclicker.domain.fields import FieldSpec
TYPE_ID = '窗口控制'
FIELDS = (FieldSpec('标题包含', '窗口标题包含', 'text', '', required=True), FieldSpec('操作', '窗口操作', 'choice', '激活', ('激活', '最小化', '最大化', '还原', '关闭', '置顶', '置底', '窗口移动', '窗口大小')), FieldSpec('报错', '未找到时报错', 'bool', True))
FIELDS += (
    FieldSpec('移动方式', '移动方式', 'choice', '左上角坐标', ('左上角坐标', '相对当前位置')),
    FieldSpec('X', '左上角 X', 'int', 0, minimum=-100000, maximum=100000),
    FieldSpec('Y', '左上角 Y', 'int', 0, minimum=-100000, maximum=100000),
    FieldSpec('宽度', '窗口宽度（像素）', 'int', 800, minimum=1, maximum=100000),
    FieldSpec('高度', '窗口高度（像素）', 'int', 600, minimum=1, maximum=100000),
    FieldSpec('大小锚点', '固定位置', 'choice', '左上角', ('左上角', '中心点')),
)
