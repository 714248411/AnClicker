"""Parameters for 网页链接提取."""
from dataclasses import replace
from anclicker.instructions.网页抓取工具.Crawl4AI网页抓取.schema import FIELDS as BASE_FIELDS
TYPE_ID = '网页链接提取'
FIELDS = tuple(replace(field, default='链接', choices=('链接',)) if field.key=='格式' else replace(field, default='网页链接') if field.key=='变量' else field for field in BASE_FIELDS)
