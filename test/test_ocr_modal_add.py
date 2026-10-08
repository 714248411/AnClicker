import os
os.environ.setdefault('QT_QPA_PLATFORM', 'offscreen')
from unittest.mock import patch
import pytest
from PySide6.QtCore import QTimer
from PySide6.QtWidgets import QApplication, QDialog, QWidget
from instructions.registry import get_instruction_spec
from instruction_workspace import InstructionWorkspace
from 数据库操作 import DatabaseOperation
from instructions.common.local_ocr_instruction import OCR_TYPES


@pytest.mark.parametrize('accepted', [True, False])
def test_region_picker_keeps_editor_modal_until_user_confirms(tmp_path, accepted):
    app = QApplication.instance() or QApplication([])
    owner = QWidget()
    owner.db = DatabaseOperation(str(tmp_path / 'ocr.db'))
    workspace = InstructionWorkspace(owner.db.db_path, owner)
    kind = 'OCR点击识别区域'
    spec = get_instruction_spec(kind)
    editor = spec.create_editor(parent=owner, context=workspace._editor_context())
    owner.show()
    picker_returned = []

    class Picker(QDialog):
        def exec(self):
            picker_returned.append(True)
            # Confirmation must occur only after region selection has returned.
            QTimer.singleShot(20, editor._accept_if_valid)
            return QDialog.DialogCode.Accepted if accepted else QDialog.DialogCode.Rejected

        def selected_region(self):
            return (10, 20, 100, 80)

    watchdog = QTimer()
    watchdog.setSingleShot(True)
    watchdog.timeout.connect(editor.reject)
    watchdog.start(3000)
    QTimer.singleShot(0, lambda: editor._run_auxiliary('区域'))
    try:
        with patch.object(type(spec), 'create_editor', return_value=editor), \
             patch('smart_capture.SmartCaptureDialog', Picker):
            command_id = workspace.add_command(kind, 120, 80)
        assert picker_returned
        assert command_id is not None
        command = workspace.repository.get_command(command_id)
        assert command.parameters['区域'] == ('(10, 20, 100, 80)' if accepted else '')
        assert any(n.command_id == command_id for n in workspace.repository.snapshot().nodes)
        assert owner.windowOpacity() == 1.0
        assert editor.windowOpacity() == 1.0
    finally:
        watchdog.stop()
        owner.close()
        editor.deleteLater()
        app.processEvents()


@pytest.mark.parametrize('kind', OCR_TYPES)
def test_palette_double_click_confirm_creates_ocr_node(tmp_path, kind):
    app = QApplication.instance() or QApplication([])
    owner = QWidget()
    owner.db = DatabaseOperation(str(tmp_path / 'doubleclick.db'))
    workspace = InstructionWorkspace(owner.db.db_path, owner)
    errors = []
    workspace._show_error = lambda *args: errors.append(args)
    opened = []
    def confirm():
        editor = app.activeModalWidget()
        if editor is not None and hasattr(editor, '_controls'):
            opened.append(editor.TYPE_ID)
            for key, value in [('区域', '10,20,100,80'), ('目标文字', '测试')]:
                if key in editor._controls:
                    editor._set_control_value(editor._controls[key], value)
            editor._accept_if_valid()
    timer = QTimer()
    timer.timeout.connect(confirm)
    timer.start(20)
    try:
        tree = workspace.palette.tree
        item = next(tree.topLevelItem(i).child(j)
                    for i in range(tree.topLevelItemCount())
                    for j in range(tree.topLevelItem(i).childCount())
                    if tree.instruction_type(tree.topLevelItem(i).child(j)) == kind)
        tree.itemDoubleClicked.emit(item, 0)
        assert not errors
        assert opened == [kind]
        commands = workspace.repository.list_commands()
        assert len(commands) == 1
        assert commands[0].type_id == kind
        assert commands[0].id in workspace.editor.scene.nodes_by_command_id
    finally:
        timer.stop()
        owner.close()
        app.processEvents()
