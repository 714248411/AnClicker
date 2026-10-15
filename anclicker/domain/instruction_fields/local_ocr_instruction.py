"""Instruction parameter schema."""
from __future__ import annotations
from anclicker.domain.fields import FieldSpec
TEXT_TYPES = ('OCR文字提取', '截图OCR', 'OCR复制')
REGION_TYPES = ('OCR识别区域返回坐标', 'OCR点击识别区域')
CLICK_TYPES = ('OCR精准找字点击', 'OCR点击识别区域', 'OCR范围找字')

def fields_for(name):
    if name == 'OCR粘贴':
        return (FieldSpec('内容来源', '粘贴内容来源（无需变量）', 'choice', '最近OCR结果', ('最近OCR结果', '剪贴板')), FieldSpec('粘贴前等待', '粘贴前等待（秒）', 'float', 0.3, minimum=0, maximum=60))
    fields = [FieldSpec('引擎', '离线引擎', 'choice', 'RapidOCR', ('RapidOCR', '微信OCR')), FieldSpec('区域', '识别区域 x,y,w,h（空为全屏）', 'text', '', required=name in ('OCR范围找字', '截图OCR', 'OCR复制'))]
    if name == 'OCR点击识别区域':
        fields.insert(0, FieldSpec('点击来源', '点击来源', 'choice', '前序OCR变量', ('前序OCR变量', '重新识别')))
    if name in TEXT_TYPES:
        if name != 'OCR文字提取':
            fields.append(FieldSpec('识别后', '识别后操作（无需变量）', 'choice', '复制到剪贴板', ('仅保存最近OCR结果', '复制到剪贴板', '复制并粘贴')))
    if name == 'OCR文字提取':
        fields.append(FieldSpec('图像路径', '图片文件（空为屏幕截图）'))
    elif name not in TEXT_TYPES:
        fields.append(FieldSpec('目标文字', '目标文字（区域模块可留空匹配全部文字框）', required=name not in REGION_TYPES))
        if name != 'OCR精准找字点击':
            fields.append(FieldSpec('匹配方式', '文字匹配方式', 'choice', '模糊' if name == 'OCR模糊找字返回坐标' else '包含', ('精准', '包含', '模糊')))
        fields += [FieldSpec('相似度', '模糊相似度 0–1', 'float', 0.8, minimum=0.01, maximum=1), FieldSpec('第几个', '排序后的第几个区域（从1开始）', 'int', 1, minimum=1, maximum=10000), FieldSpec('排序方式', '匹配区域排序', 'choice', '从上到下', ('从上到下', '离锚点最近')), FieldSpec('中心锚点', '屏幕锚点 x,y（空为识别范围中心）', 'text', ''), FieldSpec('忽略大小写', '忽略英文大小写', 'bool', True), FieldSpec('忽略空白', '忽略空白字符', 'bool', True)]
    fields.append(FieldSpec('置信度', '最低识别置信度 0–1', 'float', 0.5, minimum=0, maximum=1))
    if name not in ('截图OCR', 'OCR复制'):
        fields.append(FieldSpec('变量', '结果变量（可自定义）', 'text', '最近OCR结果' if name == 'OCR点击识别区域' else 'OCR文字' if name == 'OCR文字提取' else 'OCR坐标', required=True))
    if name == 'OCR范围找字':
        fields.append(FieldSpec('找到后', '找到后的操作', 'choice', '返回坐标', ('返回坐标', '点击区域')))
    if name in CLICK_TYPES:
        fields += [FieldSpec('动作', '点击动作', 'choice', '左键单击', ('左键单击', '左键双击', '右键单击')), FieldSpec('点击位置', '相对文字框中心偏移 x,y', 'text', '(0,0)')]
    if name.startswith('OCR等待'):
        fields += [FieldSpec('等待超时', '等待超时（秒，不含暂停）', 'float', 30, minimum=0.1, maximum=86400), FieldSpec('检测间隔', '检测间隔（秒）', 'float', 0.5, minimum=0.1, maximum=60), FieldSpec('连续次数', '连续满足次数（降低误判）', 'int', 2, minimum=1, maximum=100)]
    else:
        fields.append(FieldSpec('未找到', '未找到文字时', 'choice', '报错', ('报错', '返回空值')))
    fields.append(FieldSpec('识别超时', '单次识别超时（秒，含引擎启动）', 'float', 30, minimum=1, maximum=300))
    return tuple(fields)
