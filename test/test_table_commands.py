"""Table editing uses command IDs, not stale flowchart selection."""
import json
from unittest.mock import patch, Mock

import pytest
from qt_compat.QtCore import Qt, QMimeData, QTimer, QPointF
from qt_compat.QtGui import QContextMenuEvent
from qt_compat.QtTest import QTest
from qt_compat.QtWidgets import QApplication, QMenu, QMessageBox, QTableWidgetSelectionRange

from test.test_hidden_stop import host
from instructions.models import InstructionDraft


@pytest.fixture
def table_host(host):
    host.workspace.repository.clear()
    for i in range(4):
        host.workspace.repository.add_command(InstructionDraft('时间等待', {'时长': i, '单位': '秒'}, note=f'row {i}'))
    host.workspace.reload_graph()
    host.view_workspace.refresh_all()
    host.tabWidget.setCurrentIndex(1)
    QApplication.processEvents()
    yield host
    QApplication.clipboard().clear()


def ids(host):
    return [c.id for c in host.workspace.repository.list_commands()]


def test_toolbar_delete_uses_table_selection_and_syncs_flow(table_host):
    host = table_host
    before = ids(host)
    host.workspace.focus_command(before[0])
    table = host.view_workspace.command_table
    table.setCurrentCell(2, 3)
    with patch.object(QMessageBox, 'question', return_value=QMessageBox.StandardButton.Yes):
        assert host.delete_data() == 1
    assert ids(host) == [before[0], before[1], before[3]]
    assert table.rowCount() == 3
    assert host.workspace.repository.is_plain_chain()
    assert before[2] not in [n.command_id for n in host.workspace.repository.snapshot().nodes]


@pytest.mark.parametrize('rows', [(1, 1), (1, 3)])
def test_rectangular_copy_paste_preserves_full_commands_and_new_nodes(table_host, rows):
    host = table_host
    table = host.view_workspace.command_table
    before = host.workspace.repository.list_commands()
    edges = host.workspace.repository.snapshot().edges
    first, last = rows
    table.setRangeSelected(QTableWidgetSelectionRange(first, 2, last, 4), True)
    assert table.selected_command_ids() == [c.id for c in before[first:last+1]]
    QTest.keyClick(table, Qt.Key.Key_C, Qt.KeyboardModifier.ControlModifier)
    QTest.keyClick(table, Qt.Key.Key_V, Qt.KeyboardModifier.ControlModifier)
    after = host.workspace.repository.list_commands()
    assert [c.to_draft() for c in after[4:]] == [c.to_draft() for c in before[first:last+1]]
    assert len({c.id for c in after}) == len(after)
    assert table.rowCount() == len(after)
    assert len(host.workspace.repository.snapshot().nodes) == len(after) + 2
    assert host.workspace.repository.snapshot().edges == edges


def test_delete_rectangle_and_cancel(table_host):
    table = table_host.view_workspace.command_table
    before = ids(table_host)
    table.setRangeSelected(QTableWidgetSelectionRange(1, 2, 2, 4), True)
    with patch.object(QMessageBox, 'question', return_value=QMessageBox.StandardButton.No):
        QTest.keyClick(table, Qt.Key.Key_Delete)
    assert ids(table_host) == before
    with patch.object(QMessageBox, 'question', return_value=QMessageBox.StandardButton.Yes):
        QTest.keyClick(table, Qt.Key.Key_Delete)
    assert ids(table_host) == [before[0], before[3]]


def test_right_click_unselected_row_selects_only_that_command(table_host):
    table = table_host.view_workspace.command_table
    table.selectRow(0)
    pos = table.visualRect(table.model().index(2, 3)).center()
    observed = []
    def close_menu():
        menu = QApplication.activePopupWidget()
        observed.extend(a.text() for a in menu.actions())
        menu.close()
    QTimer.singleShot(20, close_menu)
    table.contextMenuEvent(QContextMenuEvent(QContextMenuEvent.Reason.Mouse, pos, table.mapToGlobal(pos)))
    assert table.selected_command_ids() == [ids(table_host)[2]]
    assert any('1 行' in text for text in observed)


def test_move_down_then_up_reorders_chain_and_position_slots(table_host):
    host = table_host
    before = ids(host)
    positions = [(n.x, n.y) for n in host.workspace.repository.snapshot().nodes if n.command_id]
    host.view_workspace.move_table_commands([before[0]], 4)
    assert ids(host) == before[1:] + before[:1]
    assert host.workspace.repository.is_plain_chain()
    host.view_workspace.move_table_commands([before[0]], 0)
    assert ids(host) == before
    assert [(n.x, n.y) for n in host.workspace.repository.snapshot().nodes if n.command_id] == positions


def test_serial_column_is_drag_handle_other_columns_select_cells(table_host):
    table = table_host.view_workspace.command_table
    pos = table.visualRect(table.model().index(1, 0)).center()
    QTest.mousePress(table.viewport(), Qt.MouseButton.LeftButton, pos=pos)
    assert table._row_press[1] == ids(table_host)[1]
    QTest.mouseRelease(table.viewport(), Qt.MouseButton.LeftButton, pos=pos)
    pos = table.visualRect(table.model().index(2, 3)).center()
    QTest.mousePress(table.viewport(), Qt.MouseButton.LeftButton, pos=pos)
    assert table._row_press is None
    QTest.mouseRelease(table.viewport(), Qt.MouseButton.LeftButton, pos=pos)
    assert len(table.selectedIndexes()) == 1


def test_unknown_clipboard_draft_is_atomic(table_host):
    mime = QMimeData()
    mime.setData('application/x-anclicker-commands', json.dumps([
        {'type_id': '时间等待', 'parameters': {'时长': 0}},
        {'type_id': 'unknown', 'parameters': {}}
    ]).encode())
    QApplication.clipboard().setMimeData(mime)
    before = ids(table_host)
    with patch.object(QMessageBox, 'warning') as warning:
        table_host.view_workspace.paste_table_commands()
        assert warning.called
    assert ids(table_host) == before


def test_row_drop_event_updates_model_and_flow(table_host):
    table = table_host.view_workspace.command_table
    before = ids(table_host)
    mime = QMimeData()
    mime.setData(table.ROW_MIME, str(before[0]).encode())
    event = Mock()
    event.source.return_value = table
    event.mimeData.return_value = mime
    rect = table.visualRect(table.model().index(3, 0))
    event.position.return_value = QPointF(rect.center().x(), rect.bottom()-1)
    table.dragEnterEvent(event)
    table.dragMoveEvent(event)
    assert not table._drop_line.isHidden()
    table.dropEvent(event)
    assert ids(table_host) == before[1:] + before[:1]
    assert table._drop_line.isHidden()
    assert table_host.workspace.repository.is_plain_chain()


def test_edited_table_survives_workbook_roundtrip(table_host, tmp_path):
    from openpyxl import Workbook
    from graph_repository import GraphRepository
    from 数据库操作 import DatabaseOperation
    host = table_host
    before = ids(host)
    host.view_workspace.move_table_commands([before[0]], 4)
    host.view_workspace.command_table.selectRow(1)
    host.view_workspace.copy_table_commands()
    host.view_workspace.paste_table_commands()
    repo = host.workspace.repository
    workbook = Workbook()
    repo.export_to_workbook(workbook, host.db)
    database = DatabaseOperation(str(tmp_path / 'reopened.db'))
    target = GraphRepository(database.db_path)
    target.import_from_workbook(workbook)
    assert target.list_commands() == repo.list_commands()
    assert target.snapshot().edges == repo.snapshot().edges


def test_mutations_blocked_while_running(table_host):
    before = ids(table_host)
    table_host.view_workspace.command_table.selectRow(0)
    with patch.object(table_host.command_thread, 'isRunning', return_value=True):
        assert table_host.view_workspace.delete_table_commands() == 0
        table_host.view_workspace.move_table_commands([before[0]], 4)
        table_host.view_workspace.paste_table_commands()
    assert ids(table_host) == before
