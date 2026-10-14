from test.test_hidden_stop import host
from qt_compat.QtCore import Qt,QPoint,QPointF,QEvent,QTimer
from qt_compat.QtGui import QMouseEvent,QCursor,QDrag
from qt_compat.QtWidgets import QApplication
from qt_compat.QtTest import QTest


def test_drag_blank_title_out_of_main_window(host, monkeypatch):
    host.view_workspace.editable_view_action.setChecked(True)
    host.resize(1000,700)
    host.view_workspace.show_table()
    host.view_workspace.docking.move_panel('code','right')
    dock=host.view_workspace.docking.docks['code']
    title=dock.titleBarWidget()
    QTest.qWait(50)
    point=title.rect().center()
    target=host.mapToGlobal(QPoint(host.width()+80,host.height()//2))
    QTest.mousePress(title,Qt.LeftButton,Qt.NoModifier,point)
    move=QMouseEvent(QEvent.MouseMove,QPointF(title.mapFromGlobal(target)),QPointF(target),Qt.NoButton,Qt.LeftButton,Qt.NoModifier)
    # Drive the native drag result deterministically; drop-zone hit tests are separate.
    cursor=QCursor.pos()
    QCursor.setPos(target)
    def finish_drag(drag, *_):
        assert bytes(drag.mimeData().data('application/x-anclicker-panel')) == b'code'
        return Qt.IgnoreAction
    monkeypatch.setattr(QDrag, 'exec', finish_drag)
    QApplication.sendEvent(title,move)
    QCursor.setPos(cursor)
    QTest.mouseRelease(title,Qt.LeftButton,Qt.NoModifier,title.mapFromGlobal(target))
    QTest.qWait(50)
    assert dock.isFloating()
    QTest.mouseDClick(title,Qt.LeftButton)
    QTest.qWait(30)
    assert not dock.isFloating()
