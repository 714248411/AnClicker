"""Crawl4AI single-page extraction parameters."""
from anclicker.domain.fields import FieldSpec
TYPE_ID = 'Crawl4AI网页抓取'
FIELDS = (
    FieldSpec('网址', '网页地址', required=True),
    FieldSpec('格式', '提取内容', 'choice', 'Markdown', ('Markdown', '正文', '链接', '图片', '表格', '标题', '完整结果')),
    FieldSpec('选择器', '内容 CSS 选择器（可选）'),
    FieldSpec('等待元素', '等待 CSS 元素（可选）'),
    FieldSpec('超时', '页面超时（秒）', 'int', 60, minimum=5, maximum=180),
    FieldSpec('最大字符数', '最大字符数', 'int', 20000, minimum=500, maximum=200000),
    FieldSpec('变量', '保存到变量', 'text', '网页抓取结果', required=True),
)
