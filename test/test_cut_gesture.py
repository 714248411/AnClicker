from unittest.mock import Mock
from time import monotonic
import pytest
from PySide6.QtCore import QEvent, QPointF, Qt
from PySide6.QtGui import QMouseEvent, QFocusEvent, QKeyEvent, QPainterPath
from PySide6.QtWidgets import QApplication
from test.test_connection_history import host, flow
from test.test_connection_context import layout, context


def send(view, kind, point, button, buttons):
    event = QMouseEvent(kind, QPointF(point), QPointF(view.mapToGlobal(point.toPoint())),
                        button, buttons, Qt.KeyboardModifier.NoModifier)
    QApplication.sendEvent(view.viewport(), event)


def prepare(flow):
    host, (a,b,c) = flow
    w,view = layout(host,(a,b,c))
    w._connect_nodes(a,b)
    w._connect_nodes(b,c)
    view._set_zoom(.5)
    view.centerOn(800,0)
    QApplication.processEvents()
    # Deterministic paths in a blank part of the viewport, away from node bodies.
    paths=[]
    for y,edge in zip((70,110), w.editor.scene.edges):
        path=QPainterPath(view.mapToScene(100,y))
        path.lineTo(view.mapToScene(300,y))
        edge.setPath(path)
        paths.append(path)
    return w,view


def test_cut_many_edges_one_undo_and_keeps_commands_and_camera(flow):
    w,view=prepare(flow)
    before=w.repository.snapshot()
    count=len(w._connection_history)
    zoom=view.transform().m11()
    start=QPointF(200,40)
    end=QPointF(200,140)
    send(view,QEvent.MouseButtonPress,start,Qt.RightButton,Qt.RightButton)
    send(view,QEvent.MouseMove,end,Qt.NoButton,Qt.RightButton)
    assert len(view.cutter.hits)==2
    assert w.repository.snapshot()==before # Preview is not a destructive edit.
    send(view,QEvent.MouseButtonRelease,end,Qt.RightButton,Qt.NoButton)
    assert not w.repository.snapshot().edges
    assert w.repository.snapshot().commands==before.commands
    assert len(w._connection_history)==count+1
    assert view.transform().m11()==zoom
    assert view.cutter.flashes and view.cutter.timer.isActive()
    w.undo_connections()
    assert w.repository.snapshot().edges==before.edges
    w.redo_connections()
    assert not w.repository.snapshot().edges


@pytest.mark.parametrize('cancel',['escape','focus','hide','lost_button'])
def test_cancel_never_deletes(flow,cancel):
    w,view=prepare(flow)
    before=w.repository.snapshot()
    view.cutter.begin(QPointF(200,40))
    view.cutter.move(QPointF(200,140))
    if cancel=='escape':
        view.keyPressEvent(QKeyEvent(QEvent.KeyPress,Qt.Key_Escape,Qt.NoModifier))
    elif cancel=='focus':
        view.focusOutEvent(QFocusEvent(QEvent.FocusOut))
    elif cancel=='hide':
        view.hide()
    else:
        send(view,QEvent.MouseMove,QPointF(200,160),Qt.NoButton,Qt.NoButton)
    assert not view.cutter.active and not view.cutter.hits
    assert w.repository.snapshot()==before


def test_small_click_retains_menu_and_node_right_click_is_not_cut(flow,monkeypatch):
    w,view=prepare(flow)
    menu=Mock()
    monkeypatch.setattr(view,'contextMenuEvent',menu)
    pos=QPointF(200,40)
    send(view,QEvent.MouseButtonPress,pos,Qt.RightButton,Qt.RightButton)
    send(view,QEvent.MouseButtonRelease,pos+QPointF(1,1),Qt.RightButton,Qt.NoButton)
    menu.assert_called_once()
    node=next(n for n in w.editor.scene.nodes_by_id.values() if not n.is_terminal)
    pos=QPointF(view.mapFromScene(node.sceneBoundingRect().center()))
    send(view,QEvent.MouseButtonPress,pos,Qt.RightButton,Qt.RightButton)
    assert not view.cutter.active
    send(view,QEvent.MouseButtonRelease,pos,Qt.RightButton,Qt.NoButton)


def test_running_guard_and_effect_cleanup(flow,monkeypatch):
    w,view=prepare(flow)
    before=w.repository.snapshot()
    monkeypatch.setattr(view,'can_cut_connections',lambda:False)
    send(view,QEvent.MouseButtonPress,QPointF(200,40),Qt.RightButton,Qt.RightButton)
    assert not view.cutter.active
    assert w.repository.snapshot()==before
    view.cutter.begin(QPointF(200,40))
    view.cutter.finish(QPointF(200,140))
    view.cutter.started=monotonic()-1
    view.cutter.tick()
    assert not view.cutter.flashes and not view.cutter.timer.isActive()


@pytest.mark.parametrize('zoom',[.25,1,2])
def test_cut_zoom_curves_and_dashed_edges(flow,zoom):
    w,view=prepare(flow)
    view._set_zoom(zoom)
    edge=w.editor.scene.edges[0]
    edge.link_kind=6 # Hit testing uses the complete geometric path, including dash gaps.
    path=QPainterPath(view.mapToScene(100,80))
    path.cubicTo(view.mapToScene(150,20),view.mapToScene(250,140),view.mapToScene(300,80))
    edge.setPath(path)
    view.cutter.begin(QPointF(200,30))
    view.cutter.move(QPointF(200,130))
    assert (edge.source_node.node_id,edge.target_node.node_id) in view.cutter.hits
    view.cutter.cancel()


def test_missed_swipe_does_not_add_history(flow):
    w,view=prepare(flow)
    count=len(w._connection_history)
    send(view,QEvent.MouseButtonPress,QPointF(20,20),Qt.RightButton,Qt.RightButton)
    send(view,QEvent.MouseButtonRelease,QPointF(30,120),Qt.RightButton,Qt.NoButton)
    assert len(w._connection_history)==count
    assert len(w.repository.snapshot().edges)==2
