from qt_compat.QtCore import Qt, QTimer, QPointF, QEvent
from qt_compat.QtGui import QMouseEvent
from qt_compat.QtWidgets import QApplication, QDockWidget
from qt_compat.QtTest import QTest
from test.test_hidden_stop import host


def test_menu_order_setting_and_locked_drag(host,monkeypatch):
    v=host.view_workspace;d=v.docking
    menu=next(a.menu() for a in host.menubar.actions() if a.menu() and v.editable_view_action in a.menu().actions())
    assert v.restore_view_action not in menu.actions()
    assert v.layout_menu.actions()[-1] is v.restore_view_action
    v.editable_view_action.setChecked(False)
    assert not d.editable and host.db.get_setting_value('可编辑视图')=='False'
    dock=d.docks['palette']
    assert dock.allowedAreas()==Qt.NoDockWidgetArea
    assert not dock.features() & QDockWidget.DockWidgetMovable
    d.show_targets();assert not any(t.isVisible() for t in d.targets)
    handle=host.workspace.palette.search_edit
    filter_=next(f for f in d.filters if f.key=='palette')
    filter_.eventFilter(handle,QMouseEvent(QEvent.MouseButtonPress,QPointF(10,10),Qt.LeftButton,Qt.LeftButton,Qt.NoModifier))
    filter_.eventFilter(handle,QMouseEvent(QEvent.MouseMove,QPointF(80,10),Qt.NoButton,Qt.LeftButton,Qt.NoModifier))
    assert filter_.origin is None and not dock.isFloating()
    v.editable_view_action.setChecked(True)
    assert d.editable and dock.allowedAreas()==Qt.AllDockWidgetAreas
    assert dock.features() & QDockWidget.DockWidgetMovable


def test_locked_floating_panel_embeds_only_by_context_menu(host):
    v=host.view_workspace;d=v.docking
    d.float_panel('code',True);QTest.qWait(25)
    dock=d.docks['code'];v.editable_view_action.setChecked(False)
    QTest.mouseDClick(dock.titleBarWidget(),Qt.LeftButton);QTest.qWait(25)
    assert dock.isFloating()
    selected=[]
    def choose():
        menu=QApplication.activePopupWidget()
        action=next(a for a in menu.actions() if a.text()=='融入主窗体')
        selected.append(action.text());action.trigger();menu.close()
    QTimer.singleShot(20,choose)
    d.panel_menu('code',dock.mapToGlobal(dock.rect().center()))
    QTest.qWait(25)
    assert selected and not dock.isFloating()
    assert dock.allowedAreas()==Qt.NoDockWidgetArea
    assert not d.move_panel('table','left') and not d.move_panel('flow','right')
    second=type(host)()
    try:
        assert not second.view_workspace.editable_view_action.isChecked()
        assert not second.view_workspace.docking.editable
    finally:
        second.hide();second.deleteLater();QApplication.processEvents()
