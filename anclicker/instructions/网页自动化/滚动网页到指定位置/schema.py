from anclicker.domain.fields import FieldSpec
TYPE_ID = '滚动网页到指定位置'
FIELDS = (FieldSpec('position', '页面位置', 'choice', '中间', choices=('顶部', '中间', '底部'), required=False, minimum=0, maximum=60),)
