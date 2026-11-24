"""Parameters for 网页正文提取."""
from dataclasses import replace
from anclicker.instructions.网页抓取工具.Crawl4AI网页抓取.schema import FIELDS as BASE_FIELDS
TYPE_ID = '网页正文提取'
FIELDS = tuple(replace(field, default='正文', choices=('正文',)) if field.key=='格式' else replace(field, default='网页正文') if field.key=='变量' else field for field in BASE_FIELDS)
