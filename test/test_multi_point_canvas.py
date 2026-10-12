from importlib import import_module
from types import SimpleNamespace
from qt_compat.QtCore import Qt, QPoint
from qt_compat.QtWidgets import QApplication, QDialog
from instructions.common.multi_point_canvas import MultiPointCanvas
from test.test_hidden_stop import host


def test_canvas_add_move_undo_and_more_than_one_thousand(host, monkeypatch):
    module=import_module('instructions.键鼠.多坐标点击.多坐标点击')
    points=module.parse_points(';'.join(f'{i},{i+1}' for i in range(1200)))
    canvas=MultiPointCanvas(points,host)
    monkeypatch.setattr(canvas,'local_point',lambda p:QPoint(*p))
    monkeypatch.setattr(canvas,'capture_point',lambda:(1500,1600))
    event=SimpleNamespace(button=lambda:Qt.LeftButton, buttons=lambda:Qt.LeftButton, pos=lambda:QPoint(1500,1600))
    canvas.mousePressEvent(event);canvas.mouseReleaseEvent(event)
    assert len(canvas.points)==1201 and canvas.points[-1]==(1500,1600)
    canvas.mousePressEvent(event)
    monkeypatch.setattr(canvas,'capture_point',lambda:(1520,1640))
    canvas.mouseMoveEvent(event);canvas.mouseReleaseEvent(event)
    assert len(canvas.points)==1201 and canvas.points[-1]==(1520,1640)
    canvas.undo();assert len(canvas.points)==1200
    canvas.resize(800,600);canvas.show();QApplication.processEvents()
    assert not canvas.grab().isNull()
    canvas.close()


def test_multi_point_editor_commit_cancel_and_restore_visibility(host,monkeypatch):
    module=import_module('instructions.键鼠.多坐标点击.多坐标点击')
    editor=module.InstructionEditor(parent=host)
    editor.show();QApplication.processEvents()
    editor._controls['坐标列表'].setText('10,20')
    result=[QDialog.Accepted]
    class Canvas:
        points=[(10,20),(30,40),(50,60)]
        def __init__(self,points,parent): assert points==[(10,20)]
        def exec(self): return result[0]
        def deleteLater(self): pass
    monkeypatch.setattr(module,'MultiPointCanvas',Canvas)
    editor._run_auxiliary('坐标列表')
    assert editor._controls['坐标列表'].text()=='10,20; 30,40; 50,60'
    assert editor.windowOpacity()==1 and host.windowOpacity()==1
    editor._controls['坐标列表'].setText('10,20');result[0]=QDialog.Rejected
    editor._run_auxiliary('坐标列表')
    assert editor._controls['坐标列表'].text()=='10,20'
    editor.close()


def test_enter_confirms_points_and_escape_cancels(host):
    from qt_compat.QtTest import QTest
    canvas=MultiPointCanvas([(10,20),(30,40)],host)
    canvas.show();QApplication.processEvents()
    QTest.keyClick(canvas,Qt.Key_Return)
    assert canvas.result()==QDialog.Accepted and canvas.points==[(10,20),(30,40)]
    canvas=MultiPointCanvas([(10,20)],host)
    canvas.show();QApplication.processEvents()
    QTest.keyClick(canvas,Qt.Key_Escape)
    assert canvas.result()==QDialog.Rejected
