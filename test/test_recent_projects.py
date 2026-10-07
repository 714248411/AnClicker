import os
from unittest.mock import Mock, patch
from types import SimpleNamespace

os.environ.setdefault('QT_QPA_PLATFORM', 'offscreen')
import pytest
from qt_compat.QtCore import QMimeData, QUrl, QEvent, QPointF, Qt
from qt_compat.QtGui import QDropEvent
from qt_compat.QtWidgets import QApplication, QMainWindow, QPlainTextEdit, QMessageBox
from recent_projects import RecentProjectPicker, ProjectDropFilter, dropped_project, short_path


@pytest.fixture
def app():
    return QApplication.instance() or QApplication([])


def test_short_paths_preserve_full_data_and_edit(app):
    picker = RecentProjectPicker()
    path = 'C:/parent/one/two/task.xlsx'
    picker.refresh([path, path, '/other/one/two/task.xlsx'], path)
    assert short_path(path) == '…/one/two/task.xlsx'
    assert picker.combo.count() == 2
    assert picker.combo.itemData(0) == path
    assert picker.combo.itemData(1) != path
    assert picker.combo.itemData(0, Qt.ToolTipRole) == path
    emitted = []
    picker.openRequested.connect(emitted.append)
    picker.eventFilter(picker.combo.lineEdit(), QEvent(QEvent.FocusIn))
    assert picker.combo.currentText() == path
    picker.combo.setEditText('/changed/project.xlsx')
    picker._typed()
    assert emitted == [os.path.abspath('/changed/project.xlsx')]
    picker.deleteLater()


def test_drop_only_one_local_workbook_and_preserve_instruction_mime(app, tmp_path):
    file = tmp_path / 'task.xlsx'
    file.write_bytes(b'fixture')
    mime = QMimeData()
    mime.setUrls([QUrl.fromLocalFile(str(file))])
    assert dropped_project(mime) == str(file)
    window = QMainWindow()
    target = QPlainTextEdit(window)
    window.setCentralWidget(target)
    window.statusBar = Mock()
    callback = Mock()
    filter_ = ProjectDropFilter(window, callback)
    event = QDropEvent(QPointF(10,10), Qt.CopyAction, mime, Qt.LeftButton, Qt.NoModifier)
    assert filter_.eventFilter(target.viewport(), event)
    app.processEvents()
    callback.assert_called_once_with(str(file))
    mime.setUrls([QUrl.fromLocalFile(str(file)), QUrl.fromLocalFile(str(file))])
    assert dropped_project(mime) is None
    mime = QMimeData()
    mime.setData('application/x-anclicker-instruction', b'test')
    event = QDropEvent(QPointF(10,10), Qt.CopyAction, mime, Qt.LeftButton, Qt.NoModifier)
    assert not filter_.eventFilter(target.viewport(), event)
    window.deleteLater()


@pytest.mark.parametrize('busy,answer,save_ok,expected', [
    (True, QMessageBox.Discard, True, False),
    (False, QMessageBox.Cancel, True, False),
    (False, QMessageBox.Save, False, False),
    (False, QMessageBox.Save, True, True),
    (False, QMessageBox.Discard, True, True)])
def test_guarded_project_switch(app, busy, answer, save_ok, expected):
    from Start_Win import Main_window
    window = SimpleNamespace(
        command_thread=SimpleNamespace(isRunning=lambda:busy),
        view_workspace=SimpleNamespace(recording_page=SimpleNamespace(busy=False,drafts=[],written=True)),
        workspace=SimpleNamespace(repository=SimpleNamespace(list_commands=lambda:[1])),
        db=SimpleNamespace(get_setting_value=lambda key:'old.xlsx'),
        statusBar=Mock(), add_recent_to_fileMenu=Mock(), data_import=Mock(), save_data=Mock(return_value=save_ok))
    with patch.object(QMessageBox, 'question', return_value=answer):
        Main_window.open_project_path(window, 'new.xlsx')
    assert window.data_import.called == expected


def test_outline_tracks_window_and_maximize(app):
    from window_chrome import WindowOutline
    window = QMainWindow()
    outline = WindowOutline(window)
    window.resize(640,480)
    window.show()
    app.processEvents()
    assert outline.geometry() == window.rect()
    assert window.contentsMargins().left() == 4
    window.showMaximized()
    app.processEvents()
    assert window.contentsMargins().left() == 1
    window.hide()
    window.deleteLater()
