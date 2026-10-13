from pathlib import Path
from unittest.mock import Mock

import pytest
from qt_compat.QtCore import Qt, QMimeData, QUrl, QPoint, QPointF, QDateTime, QTimer
from qt_compat.QtGui import QDragEnterEvent, QDragMoveEvent, QDropEvent
from qt_compat.QtTest import QTest
from qt_compat.QtWidgets import QApplication

from test.test_hidden_stop import host
from test.test_project_call import project, mark
import scheduled_tasks_ui as module


@pytest.fixture
def dialog(host):
    host.task_scheduler.timer.stop()
    host.task_scheduler.show_settings()
    dialog = host.task_scheduler.dialog
    QTest.qWait(10)
    yield dialog
    dialog.reject()


def mime_for(*paths):
    mime = QMimeData()
    mime.setUrls([QUrl.fromLocalFile(str(path)) for path in paths])
    return mime


def drop(widget, mime):
    enter = QDragEnterEvent(QPoint(12, 12), Qt.CopyAction, mime, Qt.LeftButton, Qt.NoModifier)
    QApplication.sendEvent(widget, enter)
    if not enter.isAccepted():
        return False
    move = QDragMoveEvent(QPoint(12, 12), Qt.CopyAction, mime, Qt.LeftButton, Qt.NoModifier)
    QApplication.sendEvent(widget, move)
    assert move.isAccepted()
    event = QDropEvent(QPointF(12, 12), Qt.CopyAction, mime, Qt.LeftButton, Qt.NoModifier)
    QApplication.sendEvent(widget, event)
    return event.isAccepted()


def test_drop_project_fills_plain_path_and_creates_task_without_loading_main(dialog, host, tmp_path):
    path = tmp_path / '定时 项目 #50%.XLSX'
    project(path, [mark('scheduled')])
    before = host.workspace.repository.snapshot()
    dialog.path.setText('previous.xlsx')
    assert drop(dialog.path, mime_for(path))
    assert Path(dialog.path.text()) == path
    assert 'file:' not in dialog.path.text()
    assert host.workspace.repository.snapshot() == before
    assert not host.task_scheduler.tasks
    dialog.create_task()
    assert len(host.task_scheduler.tasks) == 1
    assert Path(host.task_scheduler.tasks[0]['path']) == path


def test_drop_folder_selects_project_from_that_directory_after_drop(dialog, tmp_path, monkeypatch):
    folder = tmp_path / '中文目录'
    folder.mkdir()
    path = folder / '任务.xlsx'
    project(path, [mark('scheduled')])
    picker = Mock(return_value=(str(path), '项目文件 (*.xlsx)'))
    monkeypatch.setattr(module.QFileDialog, 'getOpenFileName', picker)
    assert drop(dialog.path, mime_for(folder))
    picker.assert_not_called()
    QTest.qWait(20)
    assert picker.call_count == 1
    assert Path(picker.call_args.args[2]) == folder
    assert picker.call_args.args[3] == '项目文件 (*.xlsx)'
    assert Path(dialog.path.text()) == path


def test_cancel_folder_selection_preserves_existing_project(dialog, tmp_path, monkeypatch):
    dialog.path.setText('original.xlsx')
    monkeypatch.setattr(module.QFileDialog, 'getOpenFileName', lambda *args: ('', ''))
    assert drop(dialog.path, mime_for(tmp_path))
    QTest.qWait(20)
    assert dialog.path.text() == 'original.xlsx'


def test_closed_dialog_does_not_open_queued_folder_picker(dialog, tmp_path, monkeypatch):
    picker = Mock(return_value=('', ''))
    monkeypatch.setattr(module.QFileDialog, 'getOpenFileName', picker)
    assert drop(dialog.path, mime_for(tmp_path))
    dialog.reject()
    QTest.qWait(20)
    picker.assert_not_called()


@pytest.mark.parametrize('kind', ['multiple', 'other_file', 'missing', 'remote', 'text'])
def test_invalid_drops_preserve_project_path(dialog, tmp_path, kind):
    path = tmp_path / '任务.xlsx'
    path.write_bytes(b'test')
    if kind == 'multiple':
        mime = mime_for(path, path)
    elif kind == 'other_file':
        other = tmp_path / '说明.txt'
        other.write_text('test')
        mime = mime_for(other)
    elif kind == 'missing':
        mime = mime_for(tmp_path / '不存在.xlsx')
    elif kind == 'remote':
        mime = QMimeData()
        mime.setUrls([QUrl('https://example.com/project.xlsx')])
    else:
        mime = QMimeData()
        mime.setText('file:///project.xlsx')
    dialog.path.setText('original.xlsx')
    assert not drop(dialog.path, mime)
    assert dialog.path.text() == 'original.xlsx'


def test_browse_after_drop_starts_in_current_project_folder(dialog, tmp_path, monkeypatch):
    path = tmp_path / '项目.xlsx'
    path.write_bytes(b'test')
    assert drop(dialog.path, mime_for(path))
    picker = Mock(return_value=('', ''))
    monkeypatch.setattr(module.QFileDialog, 'getOpenFileName', picker)
    dialog.browse()
    assert Path(picker.call_args.args[2]) == tmp_path
    assert Path(dialog.path.text()) == path


def readonly_task(dialog, tmp_path):
    path = tmp_path / '原项目.xlsx'
    project(path, [mark('original')])
    task_id = dialog.scheduler.add(dict(description='原任务', path=str(path), repeat='每天',
        next_run=QDateTime.currentDateTime().addDays(1).toString('yyyy-MM-ddTHH:mm:ss')))
    dialog.load_task(task_id)
    return task_id, path


@pytest.mark.parametrize('surface', ['path', 'details', 'description'])
@pytest.mark.parametrize('confirmed', [False, True])
def test_readonly_drop_confirms_before_changing_or_saving(dialog, host, tmp_path, monkeypatch, surface, confirmed):
    task_id, original = readonly_task(dialog, tmp_path)
    replacement = tmp_path / '新项目.xlsx'
    project(replacement, [mark('replacement')])
    confirm = Mock(return_value=confirmed)
    monkeypatch.setattr(dialog, '_confirm_project_replacement', confirm)
    widget = {'path': dialog.path, 'details': dialog.editor_panel,
              'description': dialog.description.viewport()}[surface]
    assert drop(widget, mime_for(replacement))
    confirm.assert_not_called()
    assert Path(dialog.path.text()) == original
    QTest.qWait(20)
    confirm.assert_called_once_with(replacement)
    assert dialog._editing == confirmed
    assert Path(dialog.path.text()) == (replacement if confirmed else original)
    assert Path(host.task_scheduler.task_by_id(task_id)['path']) == original
    assert not dialog._replacement_pending
    if confirmed:
        dialog.save_button.click()
        assert Path(host.task_scheduler.task_by_id(task_id)['path']) == replacement
        assert not dialog._editing


@pytest.mark.parametrize('confirmed,selected', [(False, False), (True, False), (True, True)])
def test_readonly_folder_drop_confirms_then_selects_project(dialog, tmp_path, monkeypatch, confirmed, selected):
    task_id, original = readonly_task(dialog, tmp_path)
    folder = tmp_path / '更换目录'
    folder.mkdir()
    replacement = folder / '项目.xlsx'
    project(replacement, [mark('new')])
    confirm = Mock(return_value=confirmed)
    picker = Mock(return_value=(str(replacement) if selected else '', '项目文件 (*.xlsx)'))
    monkeypatch.setattr(dialog, '_confirm_project_replacement', confirm)
    monkeypatch.setattr(module.QFileDialog, 'getOpenFileName', picker)
    assert drop(dialog.path, mime_for(folder))
    picker.assert_not_called()
    QTest.qWait(20)
    assert picker.call_count == int(confirmed)
    if confirmed:
        assert Path(picker.call_args.args[2]) == folder
    assert dialog._editing == (confirmed and selected)
    assert Path(dialog.path.text()) == (replacement if confirmed and selected else original)
    assert Path(dialog.scheduler.task_by_id(task_id)['path']) == original


@pytest.mark.parametrize('interruption', ['close', 'switch', 'running'])
def test_readonly_drop_cannot_modify_closed_other_or_running_task(dialog, tmp_path, monkeypatch, interruption):
    task_id, original = readonly_task(dialog, tmp_path)
    replacement = tmp_path / '新项目.xlsx'
    project(replacement, [mark('new')])
    confirm = Mock(return_value=True)
    info = Mock()
    monkeypatch.setattr(dialog, '_confirm_project_replacement', confirm)
    monkeypatch.setattr(module.QMessageBox, 'information', info)
    assert drop(dialog.path, mime_for(replacement))
    if interruption == 'close':
        dialog.reject()
    elif interruption == 'switch':
        dialog.new_task()
    else:
        dialog.scheduler.active = dict(dialog.scheduler.task_by_id(task_id))
    try:
        QTest.qWait(20)
        confirm.assert_not_called()
        assert Path(dialog.scheduler.task_by_id(task_id)['path']) == original
        assert not dialog._replacement_pending
        assert info.call_count == int(interruption == 'running')
    finally:
        dialog.scheduler.active = None


def test_task_starting_during_confirmation_cannot_be_replaced(dialog, tmp_path, monkeypatch):
    task_id, original = readonly_task(dialog, tmp_path)
    replacement = tmp_path / '新项目.xlsx'
    project(replacement, [mark('new')])
    def confirm(path):
        dialog.scheduler.active = dict(dialog.scheduler.task_by_id(task_id))
        return True
    monkeypatch.setattr(dialog, '_confirm_project_replacement', confirm)
    monkeypatch.setattr(module.QMessageBox, 'information', Mock())
    assert drop(dialog.path, mime_for(replacement))
    try:
        QTest.qWait(20)
        assert not dialog._editing
        assert Path(dialog.path.text()) == original
        assert Path(dialog.scheduler.task_by_id(task_id)['path']) == original
    finally:
        dialog.scheduler.active = None


def test_readonly_drop_rejects_text_and_batches_and_deduplicates_pending_prompt(dialog, tmp_path, monkeypatch):
    readonly_task(dialog, tmp_path)
    replacement = tmp_path / '新项目.xlsx'
    project(replacement, [mark('new')])
    confirm = Mock(return_value=False)
    monkeypatch.setattr(dialog, '_confirm_project_replacement', confirm)
    text = QMimeData()
    text.setText(str(replacement))
    assert not drop(dialog.path, text)
    assert not drop(dialog.path, mime_for(replacement, replacement))
    assert drop(dialog.path, mime_for(replacement))
    assert drop(dialog.path, mime_for(replacement))
    QTest.qWait(20)
    confirm.assert_called_once()
    assert not dialog._editing


@pytest.mark.parametrize('accepted', [False, True])
def test_replacement_confirmation_has_chinese_actions_and_safe_default(dialog, tmp_path, accepted):
    readonly_task(dialog, tmp_path)
    seen = {}
    def respond():
        box = dialog.findChild(module.QMessageBox)
        seen['text'] = box.text()
        seen['default'] = box.defaultButton().text()
        seen['detail'] = box.informativeText()
        button = next(button for button in box.buttons() if button.text() == ('更换目录' if accepted else '取消'))
        button.click()
    QTimer.singleShot(0, respond)
    assert dialog._confirm_project_replacement(tmp_path) == accepted
    assert seen['text'] == '是否更换项目目录？'
    assert seen['default'] == '取消'
    assert '保存' in seen['detail']
