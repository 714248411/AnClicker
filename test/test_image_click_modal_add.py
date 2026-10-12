import os
os.environ.setdefault('QT_QPA_PLATFORM', 'windows')
from unittest.mock import patch
import pytest
from qt_compat.QtCore import QTimer
from qt_compat.QtGui import QPixmap
from qt_compat.QtWidgets import QApplication, QDialog, QDialogButtonBox, QWidget
from instruction_workspace import InstructionWorkspace
from instructions.registry import get_instruction_spec
from 数据库操作 import DatabaseOperation

@pytest.mark.parametrize('capture', [True, False])
@pytest.mark.parametrize('outcome', ['accepted', 'cancelled', 'error'])
def test_image_selection_preserves_modal_add(tmp_path, capture, outcome):
    app = QApplication.instance() or QApplication([])
    owner = QWidget()
    owner.db = DatabaseOperation(str(tmp_path / 'project.db'))
    owner.db.writes_to_resource_folder_path(str(tmp_path))
    workspace = InstructionWorkspace(owner.db.db_path, owner)
    errors = []
    workspace._show_error = lambda *args: errors.append(args)
    spec = get_instruction_spec('图像点击')
    editor = spec.create_editor(parent=owner, context=workspace._editor_context())
    image = tmp_path / 'original.png'
    pixmap = QPixmap(100, 80)
    pixmap.fill()
    assert pixmap.save(str(image))
    editor._set_image_path(image)
    owner.show()
    owner.setWindowOpacity(.8)
    editor.setWindowOpacity(.9)
    opacity = (owner.windowOpacity(), editor.windowOpacity())
    selected = []
    class Picker(QDialog):
        def exec(self):
            selected.append(True)
            QTimer.singleShot(250, lambda: editor.ui.buttonBox.button(QDialogButtonBox.StandardButton.Ok).click())
            if outcome == 'error':
                raise RuntimeError('capture failure')
            return QDialog.DialogCode.Accepted if outcome == 'accepted' else QDialog.DialogCode.Rejected
        def selected_region(self):
            return (10, 20, 100, 80) if outcome == 'accepted' else None
        def save_selection(self, target):
            assert pixmap.save(str(target))
    watchdog = QTimer()
    watchdog.setSingleShot(True)
    watchdog.timeout.connect(editor.reject)
    watchdog.start(3000)
    QTimer.singleShot(0, lambda: editor._select_screen(capture))
    try:
        name = 'SmartCaptureDialog' if capture else '_RegionSelectionDialog'
        with patch.object(type(spec), 'create_editor', return_value=editor), \
             patch('instructions.common.image_click_editor.' + name, Picker), \
             patch('instructions.common.image_click_editor.QMessageBox.warning'):
            command_id = workspace.add_command('图像点击')
        assert selected, 'Editor modal loop exited before screenshot selection'
        assert not errors
        assert command_id is not None
        commands = workspace.repository.list_commands()
        assert len(commands) == 1
        command = commands[0]
        assert command.id in workspace.editor.scene.nodes_by_command_id
        assert (owner.windowOpacity(), editor.windowOpacity()) == opacity
        if capture and outcome == 'accepted':
            assert command.parameters['图像路径'] != str(image)
        else:
            assert command.parameters['图像路径'] == str(image)
        assert command.parameters['区域'] == ('(10, 20, 100, 80)' if not capture and outcome == 'accepted' else '')
    finally:
        watchdog.stop()
        owner.close()
        editor.deleteLater()
        app.processEvents()
