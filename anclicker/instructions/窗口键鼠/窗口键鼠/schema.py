from anclicker.domain.fields import FieldSpec
TYPE_ID = '窗口键鼠'
OPERATIONS = ('左键单击', '左键双击', '右键单击', '中键单击', '移动鼠标', '鼠标拖拽', '滚轮滑动', '组合键')
FIELDS = (
    FieldSpec('模式', '执行模式', 'choice', '前台', choices=('前台', '后台')),
    FieldSpec('窗口', '目标窗口', 'text', ''),
    FieldSpec('操作', '操作', 'choice', '左键单击', choices=OPERATIONS),
    FieldSpec('X', '相对 X', 'int', 0), FieldSpec('Y', '相对 Y', 'int', 0),
    FieldSpec('结束X', '结束 X', 'int', 0), FieldSpec('结束Y', '结束 Y', 'int', 0),
    FieldSpec('滚轮', '滚轮格数', 'int', 1),
    FieldSpec('按键', '组合键', 'text', 'ctrl+c'),
)

from anclicker.platform.background_binding import AUTO, PRESETS, PROFILES, LEGACY_AUTO
FIELDS += (FieldSpec('绑定方案', '大漠后台方案', 'choice', AUTO, choices=tuple(dict.fromkeys((*PRESETS,*PROFILES,LEGACY_AUTO)))),)
