from types import SimpleNamespace
from unittest.mock import Mock, patch
import pytest
from qt_compat.QtCore import Qt, QTimer, QPoint
from qt_compat.QtTest import QTest
from qt_compat.QtWidgets import QApplication, QWidget, QDialog
from background_window_picker import BackgroundWindowPicker, pick_background_window
from background_runtime import Windows, Size
from instructions.registry import get_instruction_spec

@pytest.fixture
def app():
    return QApplication.instance() or QApplication([])

TARGET={'窗口句柄':'321','窗口标题':'目标窗口','窗口类名':'Fixture',
        '进程ID':1234,'进程路径':'C:/fixture/app.exe'}

@pytest.mark.parametrize('child',[False,True])
def test_click_selects_window_and_returns_native_information(app,child):
    native=SimpleNamespace(cursor_position=Mock(return_value=(-500,200)),
        at_point=Mock(return_value=TARGET))
    picker=BackgroundWindowPicker(native);picker.show();QTest.qWait(10)
    QTest.mouseClick(picker,Qt.LeftButton,Qt.ControlModifier if child else Qt.NoModifier,QPoint(100,100))
    assert picker.result()==QDialog.Accepted and picker.selection==TARGET
    native.at_point.assert_called_once_with((-500,200),child=child)
    assert not picker.isVisible()
    picker.deleteLater()

def test_invalid_target_keeps_picker_open_and_escape_cancels(app):
    native=SimpleNamespace(cursor_position=lambda:(1,1),at_point=Mock(side_effect=RuntimeError('请选择应用窗口')))
    picker=BackgroundWindowPicker(native);picker.show();QTest.qWait(10)
    QTest.mouseClick(picker,Qt.LeftButton,Qt.NoModifier,QPoint(100,100))
    assert picker.isVisible() and picker.selection is None
    assert '请选择应用窗口' in picker.message
    QTest.keyClick(picker,Qt.Key_Escape)
    assert picker.result()==QDialog.Rejected and not picker.isVisible()
    picker.deleteLater()

def test_right_click_cancels_without_querying_target(app):
    native=SimpleNamespace(at_point=Mock())
    picker=BackgroundWindowPicker(native);picker.show()
    QTest.mouseClick(picker,Qt.RightButton,Qt.NoModifier,QPoint(100,100))
    assert picker.result()==QDialog.Rejected and picker.selection is None
    native.at_point.assert_not_called();picker.deleteLater()

@pytest.mark.parametrize('accept',[False,True])
def test_picking_restores_only_previously_visible_windows(app,accept):
    owner=QWidget();hidden=QWidget();owner.show()
    def finish():
        picker=next(w for w in app.topLevelWidgets() if isinstance(w,BackgroundWindowPicker) and w.isVisible())
        assert owner.isVisible() and owner.windowOpacity() == 0 and not hidden.isVisible()
        picker.selection=TARGET
        picker.accept() if accept else picker.reject()
    QTimer.singleShot(30,finish)
    assert pick_background_window(owner)==(TARGET if accept else None)
    assert owner.isVisible() and not hidden.isVisible()
    owner.close();owner.deleteLater();hidden.deleteLater();app.processEvents()

def test_editor_button_fills_all_window_fields_and_cancel_keeps_values(app):
    editor=get_instruction_spec('绑定选择窗口').create_editor()
    with patch('background_window_picker.pick_background_window',return_value=TARGET):
        editor.pickWindowButton.click()
    parameters=editor.get_draft().parameters
    assert all(parameters[k]==v for k,v in TARGET.items())
    with patch('background_window_picker.pick_background_window',return_value=None):
        editor.pickWindowButton.click()
    assert editor.get_draft().parameters==parameters
    editor.deleteLater()

def test_native_point_resolves_root_by_default_and_can_keep_child():
    windows=Windows.__new__(Windows)
    windows.gui=SimpleNamespace(WindowFromPoint=Mock(return_value=21),GetAncestor=Mock(return_value=20))
    windows.describe=Mock(side_effect=lambda hwnd:dict(TARGET,窗口句柄=str(hwnd)))
    windows.size=Mock(return_value=Size(400,300))
    assert windows.at_point((-10,20))['窗口句柄']=='20'
    assert windows.at_point((-10,20),child=True)['窗口句柄']=='21'
    windows.gui.GetAncestor.assert_called_once_with(21,2)


@pytest.mark.parametrize('accepted', [False, True])
def test_window_selection_keeps_modal_parameter_editor_open(app, accepted):
    owner = QDialog()
    owner.setWindowOpacity(0.85)
    ended_by_user = []
    selected = []
    timer = QTimer(owner)
    timer.setSingleShot(True)
    def finish_editor():
        ended_by_user.append(True)
        owner.accept()
    timer.timeout.connect(finish_editor)
    def pick():
        def finish_picker():
            picker = next(w for w in app.topLevelWidgets()
                          if isinstance(w, BackgroundWindowPicker) and w.isVisible())
            picker.selection = TARGET
            picker.accept() if accepted else picker.reject()
        QTimer.singleShot(20, finish_picker)
        selected.append(pick_background_window(owner))
        timer.start(30)
    QTimer.singleShot(0, pick)
    try:
        assert owner.exec() == QDialog.Accepted
        assert ended_by_user == [True]
        assert selected == [TARGET if accepted else None]
        assert abs(owner.windowOpacity() - 0.85) < 0.01
    finally:
        timer.stop()
        owner.close()
        owner.deleteLater()


def test_invalid_click_does_not_exit_modal_picker(app):
    native = SimpleNamespace(cursor_position=lambda: (1, 1),
        at_point=Mock(side_effect=RuntimeError('请选择应用窗口')))
    picker = BackgroundWindowPicker(native)
    cancelled_by_user = []
    timer = QTimer(picker)
    timer.setSingleShot(True)
    def cancel():
        cancelled_by_user.append(True)
        picker.reject()
    timer.timeout.connect(cancel)
    def invalid_click():
        QTest.mouseClick(picker, Qt.LeftButton, Qt.NoModifier, QPoint(100, 100))
        timer.start(30)
    QTimer.singleShot(0, invalid_click)
    try:
        assert picker.exec() == QDialog.Rejected
        assert cancelled_by_user == [True]
        assert picker.selection is None
    finally:
        timer.stop()
        picker.close()
        picker.deleteLater()
