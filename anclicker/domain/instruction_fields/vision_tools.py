"""Offline glyph, minimap and health monitor instruction fields."""
from anclicker.domain.fields import FieldSpec as F
TYPES = ('字库点击', '小地图拼接制作大地图', '多线程血量判断', 'A星寻路')
def fields_for(name):
    source = [F('截图来源','截图来源','choice','屏幕',('屏幕','窗口')), F('窗口标题','窗口标题（精确匹配）'), F('窗口句柄','窗口句柄（优先；可留空）'), F('区域','截图区域 x,y,w,h（窗口为客户区相对坐标）','text','',required=name != '多线程血量判断')]
    if name in ('制作字库','字库点击'):
        fields = source + [F('字库目录','字库目录（空为当前 Data/glyphs）'), F('目标文字','文字','text','',required=True), F('颜色模式','字色','choice','任意颜色',('红字','任意颜色'))]
        if name == '制作字库':
            return tuple(fields+[F('录入颜色','录入颜色 RGB（空为自动识别）'),F('颜色名称','颜色名称（可吸取后自动命名）')])
        return tuple(fields + [F('颜色优先','位置优先方式','choice','优先颜色',('优先颜色','不优先')),F('优先颜色','优先颜色（按顺序；例：红色;蓝色;黄色;192,40,21）','text','红色'),F('优先色配置','优先色配置','text','[]'),F('颜色容差','颜色容差','int',45,minimum=5,maximum=100),F('匹配方式','文字匹配（多目标用英文分号分隔，按填写顺序优先）','choice','包含文字',('完整匹配','包含文字')),F('相似度','最低相似度','float',.86,minimum=.5,maximum=1),F('偏移','点击偏移 x,y','text','0,0'),F('动作','点击动作','choice','左键单击',('左键单击','右键单击','左键双击')),F('变量','坐标结果变量','text','字库坐标')])
    if name == '小地图拼接制作大地图':
        return tuple(source + [F('帧数','采集帧数','int',30,minimum=2,maximum=10000),F('间隔','采集间隔（秒）','float',.5,minimum=.1,maximum=60),F('画布大小','地图画布像素','int',2048,minimum=256,maximum=4096),F('配准阈值','最低配准置信度','float',.2,minimum=.05,maximum=1),F('保存路径','保存地图 PNG','text','maps/map.png',required=True),F('变量','地图结果变量','text','大地图')])
    if name == '多线程血量判断':
        return tuple([F('检测方式','检测方式','choice','血量百分比',('守护取点检测','血量百分比')),F('守护启用','启用血条检测','choice','启用',('启用','关闭')),F('检测规则','检测规则','text','[]'),F('操作','监控操作','choice','启动监控',('启动监控','停止监控','单次判断')),F('监控名','监控名称（不同名字可同时运行）','text','血量1',required=True)] + source + [F('血量颜色','血量 RGB','text','255,0,0'),F('容差','颜色容差','int',35,minimum=0,maximum=255),F('阈值','低于此百分比触发','float',30,minimum=0,maximum=100),F('连续次数','连续满足次数','int',2,minimum=1,maximum=100),F('间隔','检测间隔（秒）','float',.2,minimum=.05,maximum=60),F('冷却','触发冷却（秒）','float',2,minimum=.1,maximum=3600),F('响应','触发动作','choice','按键',('按键','鼠标点击')),F('按键','按键（支持 ctrl+1）','text','1'),F('点击位置','鼠标坐标（同截图坐标系）','text','0,0'),F('变量','血量百分比变量','text','血量')])
    return (F('地图路径','地图图片（白色可走，黑色障碍）','text','maps/map.png',required=True),F('起始坐标','起始坐标 x,y','text','0,0',required=True),F('终点坐标','终点坐标 x,y','text','100,100',required=True),F('网格大小','网格像素（格内有障碍则不可走）','int',8,minimum=1,maximum=128),F('通行阈值','可通行灰度下限','int',200,minimum=1,maximum=255),F('保存路径','保存路线预览 PNG','text','maps/path.png',required=True),F('变量','路线坐标变量','text','寻路路线'))
