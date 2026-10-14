import os
os.environ.setdefault('QT_QPA_PLATFORM', 'windows')
from unittest.mock import patch
import pytest
from qt_compat.QtCore import QTimer, QCoreApplication, QEvent
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
        # Release the complete Qt owner tree while Python references and the
        # application are still alive, before pytest performs its final GC.
        owner.deleteLater()
        QCoreApplication.sendPostedEvents(None, QEvent.DeferredDelete)
        app.processEvents()


@pytest.mark.parametrize('when', ['before_picker', 'inside_picker', 'cancelled', 'double_start'])
def test_capture_callback_respects_editor_lifetime(tmp_path, when):
    from qt_compat import BINDING
    if BINDING == 'PySide2':
        from shiboken2 import isValid
    else:
        from shiboken6 import isValid
    from qt_compat.QtTest import QTest
    owner = QWidget()
    owner.db = DatabaseOperation(str(tmp_path / 'lifetime.db'))
    owner.db.writes_to_resource_folder_path(str(tmp_path))
    from instructions.models import ExecutionContext
    editor = get_instruction_spec('图像点击').create_editor(parent=owner,
        context=ExecutionContext(metadata={'database': owner.db}))
    image = tmp_path / 'original.png'
    pixmap = QPixmap(20,20); pixmap.fill(); assert pixmap.save(str(image))
    editor._set_image_path(image)
    owner.show(); editor.show(); owner.setWindowOpacity(.8)
    original_opacity = owner.windowOpacity()
    calls = []
    class Picker(QDialog):
        def exec(self):
            calls.append(True)
            if when == 'inside_picker':
                owner.deleteLater()
                QCoreApplication.sendPostedEvents(None, QEvent.DeferredDelete)
            return QDialog.Rejected
        def selected_region(self): return None
    try:
        with patch('instructions.common.image_click_editor.SmartCaptureDialog', Picker):
            editor._select_screen(True)
            if when == 'before_picker':
                owner.deleteLater()
                QCoreApplication.sendPostedEvents(None, QEvent.DeferredDelete)
            elif when == 'cancelled':
                editor.reject()
            elif when == 'double_start':
                assert not editor.ui.buttonBox.isEnabled()
                editor._select_screen(True)
            QTest.qWait(240)
        assert len(calls) == int(when in ('inside_picker','double_start'))
        assert list(tmp_path.glob('截图_*.png')) == []
        if isValid(editor):
            assert editor.ui.parameter_0.text() == str(image)
            assert editor.ui.buttonBox.isEnabled()
            assert owner.windowOpacity() == original_opacity
            if when == 'cancelled': assert not editor.isVisible()
    finally:
        if isValid(owner): owner.deleteLater()
        QCoreApplication.sendPostedEvents(None, QEvent.DeferredDelete)


from test.test_hidden_stop import host


def test_packaged_capture_validation_waits_for_saved_image(host):
    from ui_validation import validate_image_click_modal_add
    original = host.workspace.repository.list_commands()
    assert validate_image_click_modal_add(host)
    assert host.workspace.repository.list_commands() == original
