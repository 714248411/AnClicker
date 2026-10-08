"""Each invocation must match its own current template, even for similar images."""
from pathlib import Path
from unittest.mock import Mock, patch

import numpy as np
import pytest
from PIL import Image
import pyautogui
import pyscreeze

from instructions.models import CommandRecord, ExecutionContext
from instructions.registry import get_instruction_spec


@pytest.fixture
def targets(tmp_path):
    pixels = np.random.default_rng(19).integers(0, 256, (40, 50, 3), dtype=np.uint8)
    first = Image.fromarray(pixels)
    changed = pixels.copy()
    changed[15:25, 20:30] = 255 - changed[15:25, 20:30]
    second = Image.fromarray(changed)
    first_path, second_path = tmp_path / '图片1.png', tmp_path / '图片2.png'
    first.save(first_path)
    second.save(second_path)
    frame = Image.new('RGB', (360, 240), '#202020')
    frame.paste(first, (15, 30))
    frame.paste(second, (215, 130))
    with patch.object(pyscreeze, 'screenshot', side_effect=lambda **kwargs: frame.copy()), \
         patch.object(pyautogui, 'screenshot', side_effect=lambda **kwargs: frame.copy()), \
         patch.object(pyautogui, 'moveTo'), patch.object(pyautogui, 'click') as click:
        yield first_path, second_path, second, click


@pytest.mark.parametrize('grayscale', [False, True])
def test_image_two_selects_best_match_instead_of_first_similar_image(targets, grayscale):
    first, second, _, click = targets
    context = ExecutionContext()
    executor = get_instruction_spec('图像点击').create_executor()
    for path, expected in [(first, (40, 50)), (second, (240, 150)), (first, (40, 50))]:
        result = executor.execute(context, CommandRecord(1, '图像点击',
            {'图像路径': str(path), '灰度': grayscale, '精度': .8, '异常': '0'}))
        assert result == expected
        assert click.call_args.args == expected


def test_overwriting_template_same_path_reads_new_pixels(targets):
    first, second_path, second, click = targets
    executor = get_instruction_spec('图像点击').create_executor()
    context = ExecutionContext()
    command = CommandRecord(1, '图像点击', {'图像路径': str(first), '精度': .8, '异常': '0'})
    assert executor.execute(context, command) == (40, 50)
    second.save(first)
    assert executor.execute(context, command) == (240, 150)
    assert click.call_args.args == (240, 150)


def test_second_quick_capture_updates_preview_test_and_saved_instruction(targets, tmp_path, monkeypatch):
    from PySide6.QtCore import QRect, Qt
    from PySide6.QtGui import QPixmap
    from PySide6.QtWidgets import QApplication, QDialog, QMessageBox
    from graph_repository import GraphRepository
    from instructions.键鼠.图像点击.图像点击 import InstructionEditor
    from smart_capture import SmartCaptureDialog
    from 数据库操作 import DatabaseOperation

    app = QApplication.instance() or QApplication([])
    warnings = []
    monkeypatch.setattr(QMessageBox, 'warning', lambda *args: warnings.append(args[1:]))
    first, second, _, click = targets
    db = DatabaseOperation(str(tmp_path / 'project.db'))
    db.writes_to_resource_folder_path(str(tmp_path))
    remember = Mock()
    context = ExecutionContext(metadata={'database': db, 'remember_capture': remember})
    editor = InstructionEditor(context=context)
    editor.folder_combo.setCurrentText(str(tmp_path))
    results = []
    executor = get_instruction_spec('图像点击').create_executor()
    editor.test_requested.connect(lambda draft: results.append(executor.execute(context,
        CommandRecord(1, draft.type_id, draft.parameters))))
    repository = GraphRepository(db.db_path)
    selected_paths = []
    try:
        for source, expected in [(first, (40, 50)), (second, (240, 150))]:
            # Run the real capture save path with a new dialog and new pixels.
            with Image.open(source) as image:
                selector = SmartCaptureDialog(image=image.copy())
            selector.selection = QRect(0, 0, 50, 40)
            selector.setResult(QDialog.DialogCode.Accepted)
            with patch('instructions.common.image_click_editor.SmartCaptureDialog', return_value=selector), \
                 patch.object(selector, 'exec', return_value=QDialog.DialogCode.Accepted), \
                 patch('instructions.common.image_click_editor.QTimer.singleShot', side_effect=lambda ms, callback: callback()):
                editor.capture_button.click()
            assert not warnings
            draft = editor.get_draft()
            path = Path(draft.parameters['图像路径'])
            selected_paths.append(path)
            assert path.read_bytes() == source.read_bytes()
            assert editor.image_combo.currentText() == path.name
            preview = QPixmap(str(source)).scaled(560, 160, Qt.AspectRatioMode.KeepAspectRatio,
                                                 Qt.TransformationMode.SmoothTransformation)
            assert editor.preview.pixmap().toImage() == preview.toImage()
            remember.assert_called_with(str(path))
            editor.test_button.click()
            assert results[-1] == expected
            assert click.call_args.args == expected
        assert selected_paths[0] != selected_paths[1]
        # Persist/reload the final draft as normal running does after editing.
        repository.add_command(editor.get_draft())
        saved = repository.list_commands()[0]
        assert saved.parameters['图像路径'] == str(selected_paths[1])
        assert executor.execute(ExecutionContext(), saved) == (240, 150)
    finally:
        editor.close()
        editor.deleteLater()
        app.processEvents()


def test_flat_template_reports_problem_instead_of_matching_everywhere(targets, tmp_path):
    _, _, _, click = targets
    path = tmp_path / '纯色.png'
    Image.new('RGB', (30, 20), 'blue').save(path)
    with pytest.raises(ValueError, match='没有可区分的细节'):
        get_instruction_spec('图像点击').create_executor().execute(ExecutionContext(),
            CommandRecord(1, '图像点击', {'图像路径': str(path)}))
    click.assert_not_called()


def test_visible_image_selection_overrides_stale_backing_parameter(targets, tmp_path):
    from PySide6.QtCore import QSignalBlocker
    from PySide6.QtWidgets import QApplication
    from instructions.键鼠.图像点击.图像点击 import InstructionEditor
    from 数据库操作 import DatabaseOperation

    app = QApplication.instance() or QApplication([])
    first, second, _, click = targets
    context = ExecutionContext(metadata={'database': DatabaseOperation(str(tmp_path/'sync.db'))})
    editor = InstructionEditor(context=context)
    try:
        editor._set_image_path(first)
        # Resource-list refreshes block intermediate signals. Even if its stored
        # parameter is still image 1, executing/saving visible image 2 must fix it.
        with QSignalBlocker(editor.image_combo):
            editor.image_combo.setCurrentText(second.name)
        assert editor.ui.parameter_0.text() == str(first)
        draft = editor.get_draft()
        assert draft.parameters['图像路径'] == str(second)
        assert editor.ui.parameter_0.text() == str(second)
        result = get_instruction_spec('图像点击').create_executor().execute(context,
            CommandRecord(1, draft.type_id, draft.parameters))
        assert result == (240, 150)
        assert click.call_args.args == (240, 150)
    finally:
        editor.close()
        editor.deleteLater()
        app.processEvents()


def test_existing_command_edit_saves_and_runs_second_image(targets, tmp_path):
    from PySide6.QtWidgets import QApplication, QDialog, QWidget
    from instruction_workspace import InstructionWorkspace
    from instructions.models import InstructionDraft
    from instructions.键鼠.图像点击.图像点击 import InstructionEditor
    from 数据库操作 import DatabaseOperation

    app = QApplication.instance() or QApplication([])
    first, second, _, click = targets
    owner = QWidget()
    owner.db = DatabaseOperation(str(tmp_path/'edit.db'))
    workspace = InstructionWorkspace(owner.db.db_path, owner)
    workspace._show_error = Mock()
    original = workspace.repository.add_command(InstructionDraft('图像点击',
        {'图像路径': str(first), '精度': .8, '异常': '0'}, note='原有指令'), unconnected=True)
    def edit(dialog):
        assert dialog.get_draft().parameters['图像路径'] == str(first)
        with patch('instructions.common.image_click_editor.QFileDialog.getOpenFileName',
                   return_value=(str(second), '')):
            dialog._run_auxiliary('图像路径')
        dialog.test_button.click()  # Real workspace test connection, not a cached draft.
        assert click.call_args.args == (240, 150)
        return QDialog.DialogCode.Accepted
    try:
        with patch.object(InstructionEditor, 'exec', edit):
            assert workspace.edit_command(original.id)
        workspace._show_error.assert_not_called()
        saved = workspace.repository.get_command(original.id)
        assert saved.parameters['图像路径'] == str(second)
        assert saved.note == '原有指令'
        assert get_instruction_spec('图像点击').create_executor().execute(ExecutionContext(), saved) == (240, 150)
    finally:
        owner.close()
        owner.deleteLater()
        app.processEvents()
