import os
os.environ.setdefault('QT_QPA_PLATFORM', 'offscreen')
from pathlib import Path
from unittest.mock import Mock, patch

import pytest
from PIL import Image, ImageDraw
from PySide6.QtCore import QPoint, Qt
from PySide6.QtTest import QTest
from PySide6.QtWidgets import QApplication, QDialog, QWidget

from smart_capture import SmartCaptureDialog, edge_rectangles, snap_rectangle
from instructions.models import ExecutionContext


@pytest.fixture
def app():
    return QApplication.instance() or QApplication([])


@pytest.fixture
def fixture_screen():
    image = Image.new('RGB', (640, 400), '#eeeeee')
    draw = ImageDraw.Draw(image)
    draw.rectangle((60, 70, 460, 300), fill='white', outline='#555555', width=2)
    draw.rectangle((140, 140, 270, 195), fill='#4477aa', outline='black', width=2)
    return image


def test_nested_edge_snap_selects_inner_button(fixture_screen):
    rectangles = edge_rectangles(fixture_screen)
    selected = snap_rectangle(rectangles, 180, 165)
    assert selected is not None
    x, y, w, h = selected
    assert abs(x-140) <= 4 and abs(y-140) <= 4
    assert abs(w-130) <= 6 and abs(h-55) <= 6
    assert snap_rectangle(rectangles, 10, 10) is None


def test_click_snap_and_save_frozen_pixels(app, fixture_screen, tmp_path):
    dialog = SmartCaptureDialog(image=fixture_screen)
    dialog.resize(640, 400)
    dialog.show()
    app.processEvents()
    QTest.mouseMove(dialog, QPoint(180, 165))
    QTest.mouseClick(dialog, Qt.MouseButton.LeftButton, pos=QPoint(180, 165))
    assert dialog.result() == QDialog.DialogCode.Accepted
    path = tmp_path / '截图.png'
    dialog.save_selection(path)
    x, y, w, h = dialog.selected_region()
    with Image.open(path) as actual:
        assert actual.size == (w, h)
        assert actual.tobytes() == fixture_screen.crop((x,y,x+w,y+h)).tobytes()
    dialog.close()


def test_manual_drag_hidpi_and_escape_preserve_no_selection(app, fixture_screen):
    dialog = SmartCaptureDialog(image=fixture_screen)
    dialog.resize(320, 200)  # Two physical pixels per Qt logical pixel.
    dialog.show()
    app.processEvents()
    QTest.mousePress(dialog, Qt.MouseButton.LeftButton, pos=QPoint(10, 20))
    QTest.mouseMove(dialog, QPoint(40, 60))
    QTest.mouseRelease(dialog, Qt.MouseButton.LeftButton, pos=QPoint(40, 60))
    assert dialog.selected_region() == (20, 40, 61, 81)
    dialog = SmartCaptureDialog(image=fixture_screen)
    dialog.show()
    QTest.keyClick(dialog, Qt.Key.Key_Escape)
    assert dialog.selected_region() is None
    dialog.close()


def test_palette_capture_and_click_combine_into_one_command(app, tmp_path, fixture_screen):
    from 数据库操作 import DatabaseOperation
    from instruction_workspace import InstructionWorkspace
    from instructions.registry import get_instruction_spec
    db = DatabaseOperation(str(tmp_path/'project.db'))
    owner = QWidget()
    owner.db = db
    workspace = InstructionWorkspace(db.db_path, owner)
    workspace._show_error = Mock(side_effect=AssertionError('Unexpected UI error'))
    image = tmp_path / 'recent.png'
    fixture_screen.save(image)
    with patch('smart_capture.SmartCaptureDialog') as selector, \
         patch('smart_capture.capture_path', return_value=image), \
         patch('instruction_workspace.QTimer.singleShot', side_effect=lambda ms, fn: fn()):
        selector.return_value.exec.return_value = QDialog.DialogCode.Accepted
        workspace.quick_capture()
    assert workspace.repository.list_commands() == []
    assert workspace.palette._capture_item.data(0, Qt.ItemDataRole.UserRole) == '图像点击'
    editor_type = get_instruction_spec('图像点击').load_editor_class()
    with patch.object(editor_type, 'exec', return_value=QDialog.DialogCode.Accepted):
        workspace.add_command('图像点击', 10, 20)
    commands = workspace.repository.list_commands()
    assert len(commands) == 1
    assert commands[0].parameters['图像路径'] == str(image)
    assert commands[0].parameters['精度'] == .8
    assert commands[0].parameters['点击位置'] == '(0,0)'
    assert commands[0].parameters['区域'] == ''
    workspace.palette.set_specs(workspace.palette.specs())
    workspace.remember_capture(str(image))  # No deleted Qt-item reference after refresh.
    workspace.palette.search_edit.setText('recent.png')
    assert not workspace.palette._capture_item.isHidden()
    owner.close()


def test_capture_cancel_leaves_recent_image_unchanged(app, tmp_path):
    from 数据库操作 import DatabaseOperation
    from instruction_workspace import InstructionWorkspace
    db = DatabaseOperation(str(tmp_path/'project.db'))
    owner = QWidget()
    owner.db = db
    workspace = InstructionWorkspace(db.db_path, owner)
    workspace._recent_capture = 'before.png'
    with patch('smart_capture.SmartCaptureDialog') as selector, \
         patch('instruction_workspace.QTimer.singleShot', side_effect=lambda ms, fn: fn()):
        selector.return_value.exec.return_value = QDialog.DialogCode.Rejected
        workspace.quick_capture()
    assert workspace._recent_capture == 'before.png'
    assert workspace.repository.list_commands() == []
    selector.return_value.save_selection.assert_not_called()
    owner.close()
