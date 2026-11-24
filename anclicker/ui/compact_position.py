"""Placement preferences for the compact execution window."""
import json
from anclicker.platform.qt_compat.QtCore import QPoint
from anclicker.platform.qt_compat.QtGui import QGuiApplication

POSITION_SETTING='小化窗口起始位置'
LAST_POSITION_SETTING='小化窗口最后位置'
SIZE_MODE_SETTING='小窗口大小模式'
LAST_SIZE_SETTING='小窗口最后大小'
DEFAULT_COMPACT_SIZE=(340,460)
POSITIONS=(('左上角','top_left'),('左下角','bottom_left'),
           ('右上角','top_right'),('右下角','bottom_right'),('上次摆放位置','last'))


def place_compact_window(window):
    mode=window.db.get_setting_value(POSITION_SETTING) or 'last'
    screen=window.screen() or QGuiApplication.primaryScreen()
    if screen is None:return
    point=window.pos()
    if mode=='last':
        point=screen.availableGeometry().topLeft()
        try:
            saved=json.loads(window.db.get_setting_value(LAST_POSITION_SETTING) or '{}')
            x,y=saved['x'],saved['y']
            if type(x) is int and type(y) is int:
                point=QPoint(x,y)
                screen=QGuiApplication.screenAt(point) or screen
        except (ValueError,TypeError,KeyError):pass
    area=screen.availableGeometry()
    right=area.right()-window.frameGeometry().width()+1
    bottom=area.bottom()-window.frameGeometry().height()+1
    if mode in ('top_left','bottom_left','top_right','bottom_right'):
        point=QPoint(right if mode.endswith('right') else area.left(),
                     bottom if mode.startswith('bottom') else area.top())
    window.move(max(area.left(),min(point.x(),right)),
                max(area.top(),min(point.y(),bottom)))


def save_compact_position(window):
    if window.isMaximized() or window.isMinimized():return
    point=window.pos()
    window.db.set_setting_value(LAST_POSITION_SETTING,json.dumps({'x':point.x(),'y':point.y()}))


def resize_compact_window(window):
    width,height=DEFAULT_COMPACT_SIZE
    if (window.db.get_setting_value(SIZE_MODE_SETTING) or 'last')=='last':
        try:
            saved=json.loads(window.db.get_setting_value(LAST_SIZE_SETTING) or '{}')
            if type(saved['width']) is int and type(saved['height']) is int and saved['width']>0 and saved['height']>0:
                width,height=saved['width'],saved['height']
        except (ValueError,TypeError,KeyError):pass
    screen=window.screen() or QGuiApplication.primaryScreen()
    if screen is not None:
        area=screen.availableGeometry();width=min(width,area.width());height=min(height,area.height())
    window.resize(max(window.minimumWidth(),width),max(window.minimumHeight(),height))


def save_compact_size(window):
    if window.isMaximized() or window.isMinimized():return
    window.db.set_setting_value(LAST_SIZE_SETTING,json.dumps({'width':window.width(),'height':window.height()}))
