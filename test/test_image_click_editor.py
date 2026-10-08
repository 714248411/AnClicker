import os
os.environ.setdefault('QT_QPA_PLATFORM', 'offscreen')

from pathlib import Path
from tempfile import TemporaryDirectory
from unittest.mock import patch

import pytest
from PySide6.QtCore import QPointF
from PySide6.QtGui import QPixmap
from PySide6.QtWidgets import QApplication, QDialog
from instructions.键鼠.图像点击.图像点击 import InstructionEditor
from instructions.common.image_click_editor import ImagePositionDialog
from instructions.models import ExecutionContext, InstructionDraft
from 数据库操作 import DatabaseOperation


@pytest.fixture
def editor():
    app = QApplication.instance() or QApplication([])
    with TemporaryDirectory() as directory:
        db = DatabaseOperation(str(Path(directory) / 'test.db'))
        pixmap = QPixmap(100, 80)
        pixmap.fill()
        image = Path(directory) / '测试图片.png'
        assert pixmap.save(str(image))
        db.writes_to_resource_folder_path(directory)
        widget = InstructionEditor(context=ExecutionContext(metadata={'database': db}))
        widget._set_image_path(image)
        yield widget, image
        widget.close(); widget.deleteLater(); app.processEvents()


def test_layout_and_resources(editor):
    widget, path = editor
    assert widget.folder_combo.currentText() == str(path.parent)
    assert widget.image_combo.currentText() == path.name
    assert widget.get_draft().parameters['图像路径'] == str(path)
    assert widget.tabs.tabText(0) == '功能参数'
    assert widget.tabs.tabText(1) == '图像预览'
    assert not widget.preview.pixmap().isNull()
    assert widget.ui.auxiliary_6.text() == '调整点击位置'


def test_roundtrip_and_disabled_region(editor):
    widget, path = editor
    params = dict(widget.get_draft().parameters)
    params.update({'区域': '(10,20,300,200)', '精度': .92, '灰度': True,
                   '点击位置': '(随机,随机)', '异常': '25', '动作': '右键双击'})
    widget.load_draft(InstructionDraft(type_id='图像点击', parameters=params, repeat_count=3, note='保留'))
    assert widget.get_draft().parameters == params
    assert widget.confidence_slider.value() == 92
    assert widget.confidence_label.text() == '92%'
    assert widget.timeout_spin.value() == 25
    widget.region_group.setChecked(False)
    assert widget.get_draft().parameters['区域'] == ''
    widget.region_group.setChecked(True)
    assert widget.get_draft().parameters['区域'] == params['区域']
    widget.confidence_slider.setValue(75)
    assert widget.get_draft().parameters['精度'] == .75


def test_region_validation_and_legacy_all_screen(editor):
    widget, _ = editor
    widget.region_group.setChecked(True)
    with pytest.raises(ValueError):
        widget.get_draft()
    widget.ui.parameter_3.setText('0,0,-1,200')
    with pytest.raises(ValueError):
        widget.get_draft()
    params = {'区域': '(0,0,0,0)', '图像路径': widget.ui.parameter_0.text()}
    widget.load_draft(InstructionDraft(type_id='图像点击', parameters=params))
    assert not widget.region_group.isChecked()
    assert widget.get_draft().parameters['区域'] == ''


def test_image_position_center_offset_random(editor):
    widget, path = editor
    dialog = ImagePositionDialog(path, '(12,-7)', widget)
    assert dialog.value() == '(12,-7)'
    dialog.canvas.resize(300, 220)
    rect = dialog.canvas.image_rect()
    dialog.canvas.select_position(QPointF(rect.x()+75, rect.y()+20))
    assert dialog.value() == '(25,-20)'
    dialog.random.setChecked(True)
    assert dialog.value() == '(随机,随机)'
    assert not dialog.canvas.isEnabled()
    dialog.random.setChecked(False)
    dialog.set_offset(0, 0)
    assert dialog.value() == '(0,0)'


def test_cancel_file_picker_preserves_selection(editor):
    widget, path = editor
    with patch('instructions.common.image_click_editor.QFileDialog.getOpenFileName', return_value=('', '')):
        widget._run_auxiliary('图像路径')
    assert widget.get_draft().parameters['图像路径'] == str(path)


def test_invalid_file_prevents_accept_and_test(editor):
    widget, _ = editor
    widget._set_image_path('missing-image.png')
    with patch('instructions.common.image_click_editor.QMessageBox.warning') as warning:
        widget._accept_if_valid()
        widget._test_if_valid()
    assert warning.call_count == 2
    assert widget.result() != QDialog.DialogCode.Accepted


@pytest.mark.parametrize('capture', [True, False])
def test_screen_selection_and_cancel(editor, capture):
    widget, path = editor
    widget.show()
    selector_name = 'SmartCaptureDialog' if capture else '_RegionSelectionDialog'
    with patch('instructions.common.image_click_editor.QTimer.singleShot', side_effect=lambda delay, callback: callback()), \
         patch('instructions.common.image_click_editor.' + selector_name) as selector, \
         patch('instructions.common.image_click_editor.actions.pyautogui_module') as gui:
        selector.return_value.selected_region.return_value = None
        widget._select_screen(capture)
        gui.assert_not_called()
        assert widget.isVisible()
        assert widget.ui.parameter_0.text() == str(path)
        selector.return_value.selected_region.return_value = (10, 20, 100, 80)
        selector.return_value.save_selection.side_effect = lambda target: QPixmap(str(path)).save(str(target))
        widget._select_screen(capture)
        assert widget.isVisible()
        if capture:
            selector.return_value.save_selection.assert_called_once()
            gui.assert_not_called()
            assert Path(widget.ui.parameter_0.text()).is_file()
            assert Path(widget.ui.parameter_0.text()).name.startswith('截图_')
            selected = Path(widget.ui.parameter_0.text())
            assert widget.image_combo.currentText() == selected.name
            assert widget.image_combo.findText(selected.name) >= 0
            assert widget.get_draft().parameters['图像路径'] == str(selected)
            assert not widget.preview.pixmap().isNull()
        else:
            assert widget.region_group.isChecked()
            assert widget.get_draft().parameters['区域'] == '(10, 20, 100, 80)'


def test_random_offset_stays_inside_image(editor):
    from instructions.common.actions import image_random_offset
    _, path = editor
    with patch('instructions.common.actions.random.randint', side_effect=lambda low, high: high):
        assert image_random_offset({'图像路径': str(path)}) == (49, 39)


def test_consecutive_capture_selects_latest_and_failure_preserves_it(editor):
    widget, original = editor
    with patch('instructions.common.image_click_editor.QTimer.singleShot', side_effect=lambda delay, callback: callback()), \
         patch('instructions.common.image_click_editor.SmartCaptureDialog') as selector, \
         patch('instructions.common.image_click_editor.actions.pyautogui_module') as gui, \
         patch('instructions.common.image_click_editor.QMessageBox.warning') as warning:
        selector.return_value.selected_region.return_value = (10, 20, 100, 80)
        selector.return_value.save_selection.side_effect = lambda target: QPixmap(str(original)).save(str(target))
        previous = str(original)
        for _ in range(2):
            widget.capture_button.click()
            selected = widget.get_draft().parameters['图像路径']
            assert selected != previous
            assert widget.image_combo.currentText() == Path(selected).name
            assert widget.image_combo.findText(Path(selected).name) >= 0
            assert not widget.preview.pixmap().isNull()
            previous = selected
        selector.return_value.save_selection.side_effect = OSError('disk full')
        widget.capture_button.click()
        warning.assert_called_once()
        assert widget.get_draft().parameters['图像路径'] == previous
        assert widget.image_combo.currentText() == Path(previous).name
        assert widget.isVisible()
