from types import SimpleNamespace
from unittest.mock import Mock, patch
import pytest
from qt_compat.QtCore import Qt, QPoint, QTimer
from qt_compat.QtGui import QColor
from qt_compat.QtTest import QTest
from qt_compat.QtWidgets import QDialog, QWidget
from instructions.registry import get_instruction_spec
from instructions.common import actions
from instructions.键鼠.颜色判断.颜色判断 import ColorPointSelectionDialog


@pytest.mark.parametrize('outcome',['accept','escape','pixel_error','cancel_after_click'])
def test_color_coordinate_pick_is_atomic_and_samples_without_overlay(outcome):
    parent=QWidget();parent.setWindowOpacity(.8);parent.show()
    editor=get_instruction_spec('颜色判断').create_editor(parent)
    editor.setWindowOpacity(.9)
    editor._controls['坐标'].setText('1,2')
    editor._controls['颜色'].setText('#ABCDEF')
    selected=[]
    def create_picker(key):
        picker=ColorPointSelectionDialog(editor)
        selected.append(picker)
        def select():
            if outcome=='escape':
                QTest.keyClick(picker,Qt.Key_Escape)
            else:
                QTest.mouseClick(picker,Qt.LeftButton,pos=QPoint(20,20))
                if outcome=='cancel_after_click':QTest.keyClick(picker,Qt.Key_Escape)
        QTimer.singleShot(20,select)
        return picker
    def acquire():
        editor.ui.auxiliary_0.click()
        assert editor.isVisible() and parent.isVisible()
        editor.accept()
    gui=Mock()
    gui.position.return_value=SimpleNamespace(x=-123,y=456)
    def sample(x,y):
        assert selected[-1].windowOpacity()==0
        assert parent.windowOpacity()==0 and editor.windowOpacity()==0
        if outcome=='pixel_error':raise OSError('pixel unavailable')
        return 17,34,51
    gui.pixel.side_effect=sample
    QTimer.singleShot(0,acquire)
    with patch.object(editor,'_create_point_selector',side_effect=create_picker), \
         patch.object(actions,'pyautogui_module',return_value=gui), \
         patch('instructions.common.editor.QMessageBox.warning') as warning:
        assert editor.exec()==QDialog.Accepted
        assert warning.call_count==int(outcome=='pixel_error')
    assert editor.windowOpacity()==pytest.approx(.9,abs=.01)
    assert parent.windowOpacity()==pytest.approx(.8,abs=.01)
    if outcome=='accept':
        assert editor._controls['坐标'].text()=='-123,456'
        assert editor._controls['颜色'].text()=='#112233'
        gui.pixel.assert_called_once_with(-123,456)
    else:
        assert editor._controls['坐标'].text()=='1,2'
        assert editor._controls['颜色'].text()=='#ABCDEF'
        if outcome!='pixel_error':gui.pixel.assert_not_called()
    parent.close();editor.deleteLater();parent.deleteLater()


@pytest.mark.parametrize('accepted',[True,False])
def test_independent_color_picker_keeps_coordinates_and_allows_manual_edits(accepted):
    editor=get_instruction_spec('颜色判断').create_editor()
    try:
        editor._controls['坐标'].setText('123,456')
        editor._controls['颜色'].setText('#ABCDEF')
        color=QColor('#123456') if accepted else QColor()
        with patch('instructions.键鼠.颜色判断.颜色判断.QColorDialog.getColor',return_value=color):
            editor.ui.auxiliary_1.click()
        assert editor._controls['坐标'].text()=='123,456'
        assert editor._controls['颜色'].text()==('#123456' if accepted else '#ABCDEF')
        assert not editor._controls['坐标'].isReadOnly() and not editor._controls['颜色'].isReadOnly()
        editor._controls['坐标'].setText('-20,30')
        editor._controls['颜色'].setText('10,20,30')
        params=editor.get_draft().parameters
        assert params['坐标']=='-20,30' and params['颜色']=='10,20,30'
    finally:
        editor.deleteLater()
