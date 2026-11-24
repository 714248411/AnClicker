from anclicker.domain.fields import FieldSpec
TYPE_ID = '窗口多坐标点击'
OPERATIONS = ('左键单击', '左键双击', '右键单击', '中键单击')
FIELDS = (FieldSpec('窗口', '目标窗口', 'text', ''),
          FieldSpec('模式', '执行模式', 'choice', '前台', ('前台', '后台')),
          FieldSpec('操作', '点击方式', 'choice', '左键单击', OPERATIONS),
          FieldSpec('坐标列表', '窗口相对坐标列表', 'text', ''),
          FieldSpec('间隔', '点击间隔（秒）', 'float', 0.2, minimum=0, maximum=3600))

from anclicker.platform.background_binding import AUTO, PRESETS, PROFILES, LEGACY_AUTO
FIELDS += (FieldSpec('绑定方案', '大漠后台方案', 'choice', AUTO, choices=tuple(dict.fromkeys((*PRESETS,*PROFILES,LEGACY_AUTO)))),)
