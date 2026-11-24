from anclicker.domain.fields import FieldSpec
TYPE_ID = '滚动元素到页面中心'
FIELDS = (FieldSpec('selector', '目标元素', 'text', '', choices=(), required=True, minimum=0, maximum=60),
FieldSpec('by', '定位方式', 'choice', '智能匹配', choices=('智能匹配', 'CSS选择器', 'XPath', '文本内容', '锚点定位'), required=False, minimum=0, maximum=60),
FieldSpec('behavior', '滚动方式', 'choice', '平滑滚动', choices=('平滑滚动', '立即定位'), required=False, minimum=0, maximum=60),
FieldSpec('timeout', '等待元素（秒）', 'float', 10, choices=(), required=False, minimum=0, maximum=60),
FieldSpec('settle', '滚动后等待（秒）', 'float', 0.3, choices=(), required=False, minimum=0, maximum=30),
FieldSpec('anchor', '辅助锚点', 'text', '', choices=(), required=False, minimum=0, maximum=60),
FieldSpec('anchorRel', '目标相对锚点', 'choice', '下方', choices=('下方', '上方', '右侧', '左侧', '内部', '相邻'), required=False, minimum=0, maximum=60),)
