"""Lock hit testing, persistence and atomic grouped reorder regressions."""
import os
os.environ.setdefault('QT_QPA_PLATFORM', 'offscreen')
import sys
from pathlib import Path
sys.path.insert(0, str(Path(__file__).resolve().parents[1]))
import sqlite3
import tempfile
from types import SimpleNamespace, MethodType
from anclicker.domain.instructions import InstructionDraft, CommandRecord
from anclicker.domain.step_folding import folding_groups, locked_move_ids
from anclicker.storage.graph_repository import GraphRepository
from anclicker.ui.instruction_table import InstructionTableWidget, InstructionTableController, FOLD_LOCK_ROLE, fold_lock_rect
from anclicker.ui.instruction_workspace import InstructionWorkspace
from anclicker.platform.qt_compat.QtWidgets import QApplication, QTableWidgetItem
from anclicker.platform.qt_compat.QtCore import Qt, QPointF, QEvent
from anclicker.platform.qt_compat.QtGui import QMouseEvent
from anclicker.instructions.registry import get_instruction_spec

app = QApplication.instance() or QApplication([])
class Workspace(SimpleNamespace): pass

def ordinary(): return InstructionDraft('时间等待', {'时长': 0})
def repo_at(path):
    with sqlite3.connect(path) as db:
        GraphRepository.initialize_schema(db)
    db.close()
    return GraphRepository(str(path))

with tempfile.TemporaryDirectory() as folder:
    repo = repo_at(Path(folder) / 'lock.db')
    ids = repo.append_recording([ordinary(), InstructionDraft('折叠步骤', {'下方条数': 2}),
                                 ordinary(), ordinary(), ordinary(), ordinary()])
    table = InstructionTableWidget(0, 7)
    table.resize(950, 400)
    errors = []
    def refresh():
        commands = repo.list_commands()
        table.setRowCount(len(commands))
        for row, command in enumerate(commands):
            for column in range(7):
                item = QTableWidgetItem(command.type_id if column == 2 else str(row+1))
                item.setData(Qt.UserRole, command.id)
                item.setToolTip(item.text())
                table.setItem(row, column, item)
        table.update_comment_ranges(repo.snapshot())
    host = Workspace(repository=repo, _check_parameter_save_allowed=lambda: None,
                     reload_graph=lambda *_: refresh(), graphFinalized=SimpleNamespace(emit=lambda *_: refresh()),
                     _show_error=lambda title, error: errors.append(error))
    host.toggle_step_lock = MethodType(InstructionWorkspace.toggle_step_lock, host)
    workspace = Workspace(window=SimpleNamespace(workspace=host, statusBar=SimpleNamespace(showMessage=lambda *args: None)),
                          command_table=table, _table_mutation_allowed=lambda: True)
    controller = InstructionTableController(workspace)
    workspace._select_table_ids = controller._select_table_ids
    refresh(); table.show(); app.processEvents()
    assert table.item(1, 2).data(FOLD_LOCK_ROLE) is False
    fold_events, edit_events, lock_events = [], [], []
    table.stepFoldRequested.connect(fold_events.append)
    table.cellDoubleClicked.connect(lambda *args: edit_events.append(args))
    table.stepLockRequested.connect(lock_events.append)
    table.stepLockRequested.connect(lambda cid: host.toggle_step_lock(cid))
    point = fold_lock_rect(table.visualRect(table.model().index(1, 2))).center()
    assert table._lock_at(point) == ids[1]
    for kind, buttons in ((QEvent.MouseButtonPress, Qt.LeftButton), (QEvent.MouseButtonRelease, Qt.NoButton)):
        event = QMouseEvent(kind, QPointF(point), QPointF(table.viewport().mapToGlobal(point)), Qt.LeftButton, buttons, Qt.NoModifier)
        app.sendEvent(table.viewport(), event)
    assert lock_events == [ids[1]] and not fold_events and not edit_events
    assert not table._fold_click_timer.isActive()
    assert repo.get_command(ids[1]).parameters['整体锁定'] is True
    assert table.item(1, 2).data(FOLD_LOCK_ROLE) is True
    assert GraphRepository(repo.db_path).get_command(ids[1]).parameters['整体锁定'] is True
    # Folded group moves to the end in existing order, with children still folded.
    controller.move_table_commands([ids[1]], 6)
    assert [c.id for c in repo.list_commands()] == [ids[0], ids[4], ids[5], ids[1], ids[2], ids[3]]
    assert folding_groups(repo.list_commands())[ids[1]]['members'] == set(ids[2:4])
    assert table.isRowHidden(4) and table.isRowHidden(5)
    assert [c.id for c in repo.validate_graph().commands] == [c.id for c in repo.list_commands()]
    # Moving an expanded member carries the locked group too.
    draft = repo.get_command(ids[1]).to_draft(); draft.parameters['已折叠'] = False
    repo.update_command(ids[1], draft); refresh()
    controller.move_table_commands([ids[2]], 0)
    assert [c.id for c in repo.list_commands()] == [ids[1], ids[2], ids[3], ids[0], ids[4], ids[5]]
    assert all(not table.isRowHidden(row) for row in range(6))
    # Settings preserve the lock, unlocking makes the marker a single moving row.
    editor = get_instruction_spec('折叠步骤').create_editor(draft=repo.get_command(ids[1]).to_draft())
    assert editor.get_draft().parameters['整体锁定'] is True
    editor.close()
    host.toggle_step_lock(ids[1])
    controller.move_table_commands([ids[1]], 6)
    assert [c.id for c in repo.list_commands()] == [ids[2], ids[3], ids[0], ids[4], ids[5], ids[1]]
    assert not repo.get_command(ids[1]).parameters['整体锁定']
    assert not errors
    table.close()
    # Disjoint absolute ranges must retain the same IDs after packing/moving.
    ranged = repo_at(Path(folder) / 'range.db')
    rid = ranged.append_recording([InstructionDraft('折叠步骤', {'整体锁定': True, '按条数': False,
        '按范围': True, '步骤范围': '3;5-6'})] + [ordinary() for _ in range(6)])
    members = folding_groups(ranged.list_commands())[rid[0]]['members']
    selected = locked_move_ids(ranged.list_commands(), [rid[0]])
    ordered = [cid for cid in rid if cid not in selected] + [cid for cid in rid if cid in selected]
    ranged.reorder_table_commands(ordered)
    assert folding_groups(ranged.list_commands())[rid[0]]['members'] == members
    # Invalid direct reorder rolls back, rather than splitting the locked group.
    before = ranged.snapshot()
    try:
        ranged.reorder_table_commands(list(reversed(ordered)))
    except ValueError:
        pass
    else:
        raise AssertionError('Locked owner moved behind members')
    assert ranged.snapshot() == before
    # Lock closure supports nested locks without duplicate membership.
    commands = [CommandRecord(1, '折叠步骤', {'整体锁定': True, '下方条数': 3}, order=0),
        CommandRecord(2, '折叠步骤', {'整体锁定': True, '下方条数': 2}, order=1),
        CommandRecord(3, '时间等待', order=2), CommandRecord(4, '时间等待', order=3),
        CommandRecord(5, '时间等待', order=4)]
    assert locked_move_ids(commands, [3]) == {1, 2, 3, 4}
print('PASS: default unlocked, lock click isolation, persistence, collapsed/expanded whole moves, unlock single moves, range relocation, nested locks and transactional rollback')
