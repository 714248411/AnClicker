"""Window arrangement parameter contract."""
from anclicker.domain.fields import FieldSpec
from anclicker.domain.window_arrangement import LAYOUT_MODES
TYPE_ID='窗口排布'
FIELDS=(FieldSpec('窗口列表','窗口列表','text','[]'),
        FieldSpec('屏幕','屏幕选择','text','主屏幕'),
        FieldSpec('排布方式','排布方式','choice','网格',LAYOUT_MODES),
        FieldSpec('窗口大小','窗口大小','choice','自动',('自动','自定义')),
        FieldSpec('宽度','宽度','int',960,minimum=50,maximum=20000),
        FieldSpec('高度','高度','int',640,minimum=50,maximum=20000),
        FieldSpec('排布方向','排布方向','choice','横向优先',('横向优先','纵向优先')),
        FieldSpec('行数','行数','int',2,minimum=1,maximum=100),
        FieldSpec('列数','列数','int',3,minimum=1,maximum=100),
        FieldSpec('边距','屏幕边距','int',8,minimum=-20000,maximum=500),
        FieldSpec('间距','窗口间距','int',8,minimum=-20000,maximum=500),
        FieldSpec('自动补位','自动补位','bool',False),
        FieldSpec('保持比例','游戏增强：保持内容比例','bool',False),
        FieldSpec('起点X','首窗左上角 X','int',0,minimum=-100000,maximum=100000),
        FieldSpec('起点Y','首窗左上角 Y','int',0,minimum=-100000,maximum=100000),
        FieldSpec('X间距','X 间距','int',32,minimum=-20000,maximum=20000),
        FieldSpec('Y间距','Y 间距','int',32,minimum=-20000,maximum=20000),
        FieldSpec('对角间距','斜向间距','int',32,minimum=-20000,maximum=20000),
        FieldSpec('排布版本','排布版本','int',2,minimum=1,maximum=2))
