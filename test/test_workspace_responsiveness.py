"""Regressions for long workflows, editing continuity and narrow UI."""
from unittest.mock import patch
import pytest
from qt_compat.QtCore import Qt
from qt_compat.QtTest import QTest
from test.test_hidden_stop import host
from instructions.models import InstructionDraft
from view_workspace import CODE_SETTING


def fill_table(host, count=6):
    repo = host.workspace.repository
    repo.clear()
    ids = repo.append_recording([InstructionDraft('时间等待', {'时长': i}) for i in range(count)], connect=False)
    host.view_workspace.show_table()
    host.view_workspace.refresh_table()
    return ids


def test_table_refresh_reuses_unchanged_cells(host):
    fill_table(host, 300)
    view = host.view_workspace
    with patch.object(view.command_table, 'setItem', wraps=view.command_table.setItem) as replace:
        view.refresh_table()
        assert replace.call_count == 0


def test_selection_follows_command_after_preceding_row_removed(host):
    ids = fill_table(host)
    table = host.view_workspace.command_table
    table.setCurrentCell(3, 3)
    host.workspace.repository.delete_commands([ids[0]], preserve_flow=False)
    host.view_workspace.refresh_table()
    assert table.selected_command_ids() == [ids[3]]
    assert table.currentItem().data(Qt.UserRole) == ids[3]
    assert table.currentColumn() == 3


def test_code_autosave_waits_for_typing_pause(host):
    view = host.view_workspace
    view.show_code()
    with patch.object(host.db, 'set_setting_value', wraps=host.db.set_setting_value) as save:
        view.code_editor.insertPlainText('# 编辑开始')
        QTest.qWait(220)
        view.code_editor.insertPlainText('继续输入')
        QTest.qWait(180)
        assert not [call for call in save.call_args_list if call.args[0] == CODE_SETTING]
        QTest.qWait(240)
        writes = [call for call in save.call_args_list if call.args[0] == CODE_SETTING]
        assert len(writes) == 1
        assert writes[0].args[1] == view.code_editor.toPlainText()


def test_switching_code_view_preserves_caret_and_undo(host):
    view = host.view_workspace
    view.show_code()
    view.code_editor.insertPlainText('# 保留编辑位置\n')
    view._save_code()
    pos = view.code_editor.textCursor().position()
    assert view.code_editor.document().isUndoAvailable()
    view.show_table()
    view.show_code()
    assert view.code_editor.textCursor().position() == pos
    assert view.code_editor.document().isUndoAvailable()


@pytest.mark.parametrize('theme', ['light', 'dark'])
def test_enlarged_search_text_fits_and_log_is_literal(host, theme):
    view = host.view_workspace
    view.theme_mode = theme
    view._apply_theme()
    view.show_table()
    QTest.qWait(100)
    view.interface_scale.change(10)
    QTest.qWait(100)
    search = host.workspace.palette.search_edit
    assert search.height() >= search.fontMetrics().height() + 4
    host.clear_textEdit()
    host.send_message('匹配 <button> & <span> 保留原文')
    assert '匹配 <button> & <span> 保留原文' in host.textEdit.toPlainText()


def test_refresh_updates_changed_parameters_without_losing_selection(host):
    ids = fill_table(host)
    table = host.view_workspace.command_table
    table.setCurrentCell(2, 3)
    unchanged = table.item(0, 3)
    host.workspace.repository.update_command(ids[2], InstructionDraft('时间等待', {'时长': 42}, note='新备注'))
    host.view_workspace.refresh_table()
    assert table.item(0, 3) is unchanged
    assert '42' in table.item(2, 3).text()
    assert table.item(2, 6).text() == '新备注'
    assert table.selected_command_ids() == [ids[2]]


def test_deleted_selected_command_does_not_select_next_command(host):
    ids = fill_table(host)
    table = host.view_workspace.command_table
    table.setCurrentCell(2, 3)
    host.workspace.repository.delete_commands([ids[2]], preserve_flow=False)
    host.view_workspace.refresh_table()
    assert table.selected_command_ids() == []
    assert table.currentItem() is None


def test_explicit_code_save_cancels_pending_timer(host):
    view = host.view_workspace
    view.show_code()
    view.code_editor.insertPlainText('# 保存最新编辑')
    with patch.object(host.db, 'set_setting_value', wraps=host.db.set_setting_value) as save:
        view._save_code()
        QTest.qWait(420)
        assert len([call for call in save.call_args_list if call.args[0] == CODE_SETTING]) == 1


def test_scheduled_log_messages_are_batched(host):
    from unittest.mock import Mock
    host.clear_textEdit()
    worker = Mock()
    worker.isRunning.return_value = True
    host.task_scheduler.worker = worker
    try:
        for i in range(100):
            host.send_message(f'定时日志 {i}')
        assert host._runtime_message_timer.isActive()
        assert not host.textEdit.toPlainText()
        QTest.qWait(80)
        assert '定时日志 99' in host.textEdit.toPlainText()
        assert not host._runtime_message_timer.isActive()
    finally:
        host.task_scheduler.worker = None
