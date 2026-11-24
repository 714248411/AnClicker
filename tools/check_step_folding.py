"""Regression checks for folding persistence, Qt presentation and click gestures."""
import os
os.environ.setdefault('QT_QPA_PLATFORM', 'offscreen')
import sys
from pathlib import Path
sys.path.insert(0, str(Path(__file__).resolve().parents[1]))
import sqlite3
import tempfile
from types import SimpleNamespace
from anclicker.domain.step_folding import parse_ranges, folding_groups, hidden_steps, validate_parameters
from anclicker.domain.instructions import InstructionDraft
from anclicker.instructions.registry import get_instruction_spec, INSTRUCTION_SPECS
from anclicker.storage.graph_repository import GraphRepository
from anclicker.platform.qt_compat.QtWidgets import QApplication, QTableWidgetItem, QMenu
from anclicker.platform.qt_compat.QtCore import Qt, QPoint, QEventLoop, QTimer
from anclicker.platform.qt_compat.QtGui import QContextMenuEvent
from anclicker.ui.instruction_table import InstructionTableWidget, INDENT_DEPTH_ROLE
from anclicker.ui.instruction_workspace import InstructionWorkspace
from anclicker.ui.node_editor.widget import NodeEditorWidget
def wait(ms):
    loop = QEventLoop()
    QTimer.singleShot(ms, loop.quit)
    loop.exec_()

app = QApplication.instance() or QApplication([])
for value in ('7-9', '7,9', '７，９', '7—9', '7、9', '7至9'):
    assert parse_ranges(value) == [(7, 9)], value
assert parse_ranges('2-3；5，7') == [(2, 3), (5, 7)]
for value in ('0-2', '9-7', '7,', 'bad', '', '-2', '1,2,3'):
    try:
        parse_ranges(value)
    except ValueError:
        pass
    else:
        raise AssertionError(value)
try:
    validate_parameters({'按条数': False, '按范围': False})
except ValueError:
    pass
else:
    raise AssertionError('No method accepted')

spec = get_instruction_spec('折叠步骤')
editor = spec.create_editor()
editor.by_range.setChecked(True)
editor.ranges.setValue(5)
editor.count.setValue(2)
draft = editor.get_draft()
assert spec.create_executor().execute(None, None) is None
with tempfile.TemporaryDirectory() as folder:
    path = Path(folder) / 'test.db'
    with sqlite3.connect(path) as db:
        GraphRepository.initialize_schema(db)
    db.close()
    repo = GraphRepository(str(path))
    ids = repo.append_recording([draft] + [InstructionDraft('时间等待', {'时长': 0}) for _ in range(5)]
                                + [InstructionDraft('折叠步骤', {'下方条数': 100})]
                                + [InstructionDraft('时间等待', {'时长': 0})])
    snapshot = repo.snapshot()
    groups = folding_groups(snapshot.commands)
    assert groups[ids[0]]['members'] == set(ids[1:5])
    assert groups[ids[6]]['number'] == 2
    assert groups[ids[6]]['members'] == {ids[7]}
    assert hidden_steps(groups) == set(ids[1:5] + [ids[7]])
    assert [c.id for c in repo.validate_graph().commands] == ids
    table = InstructionTableWidget(len(ids), 7)
    for row, command in enumerate(snapshot.commands):
        for col in range(7):
            item = QTableWidgetItem(command.type_id if col == 2 else str(row+1))
            item.setData(Qt.UserRole, command.id)
            item.setToolTip(item.text())
            table.setItem(row, col, item)
    table.update_comment_ranges(snapshot)
    assert table.isRowHidden(1) and not table.isRowHidden(0)
    assert table.item(0, 2).text().startswith('▸')
    assert '1' in table.item(0, 2).text() and '2' in table.item(6, 2).text()
    assert table.item(1, 2).text() == '时间等待' and table.item(1, 2).data(INDENT_DEPTH_ROLE) == 1
    assert table.item(5, 2).text() == '时间等待', 'Outside the range has no indent'
    assert table.item(6, 2).text().startswith('▸'), 'Sibling groups share the same level'
    # An outer group containing another marker adds one indentation level.
    from dataclasses import replace
    nested = list(snapshot.commands)
    nested[0] = replace(nested[0], parameters={'下方条数': 100, '已折叠': False})
    table.step_groups = folding_groups(nested)
    table.apply_comment_folds()
    assert table.item(6, 2).text().startswith('▸') and table.item(6, 2).data(INDENT_DEPTH_ROLE) == 1
    assert table.item(7, 2).text() == '时间等待' and table.item(7, 2).data(INDENT_DEPTH_ROLE) == 2
    table.update_comment_ranges(snapshot)

    graph = NodeEditorWidget()
    graph.load_graph(snapshot.nodes, snapshot.edges, INSTRUCTION_SPECS, allow_incomplete=True)
    owner = SimpleNamespace(editor=graph)
    InstructionWorkspace._apply_step_folds(owner, snapshot)
    assert not graph.scene.nodes_by_command_id[ids[1]].isVisible()
    assert graph.scene.nodes_by_command_id[ids[0]].isVisible()
    for edge in graph.scene.edges:
        assert edge.isVisible() == (edge.source_node.isVisible() and edge.target_node.isVisible())
    toggles = []
    table.stepFoldRequested.connect(toggles.append)
    table.cellClicked.emit(0, 2)
    wait(QApplication.doubleClickInterval()+80)
    assert toggles == [ids[0]]
    table.cellClicked.emit(0, 2)
    table.cellDoubleClicked.emit(0, 2)
    table.cellClicked.emit(0, 2)  # second release after double click
    wait(QApplication.doubleClickInterval()+80)
    assert toggles == [ids[0]], 'Double click must only edit'
    table.cellClicked.emit(0, 3)
    wait(QApplication.doubleClickInterval()+80)
    assert toggles == [ids[0]]
    table.loop_ranges = {ids[5]: {ids[6], ids[7]}}
    table.cellClicked.emit(5, 2)
    wait(QApplication.doubleClickInterval()+80)
    assert ids[5] in table.collapsed_loops and table.isRowHidden(6)
    table.cellClicked.emit(5, 2)
    wait(QApplication.doubleClickInterval()+80)
    assert ids[5] not in table.collapsed_loops and not table.isRowHidden(6)
    # Expanding preserves every command and edge, and persists across reopening.
    expanded = repo.get_command(ids[0]).to_draft()
    expanded.parameters['已折叠'] = False
    repo.update_command(ids[0], expanded)
    reopened = GraphRepository(str(path)).snapshot()
    assert reopened.edges == snapshot.edges
    assert [c.id for c in reopened.commands] == ids
    table.update_comment_ranges(reopened)
    InstructionWorkspace._apply_step_folds(owner, reopened)
    assert not table.isRowHidden(1)
    assert table.item(0, 2).text().startswith('▾')
    assert graph.scene.nodes_by_command_id[ids[1]].isVisible()
    assert table.isRowHidden(7), 'Independent collapsed group must remain collapsed'
    # Numbering follows table order after deletion; overlarge range is clamped.
    repo.delete_commands([ids[0]])
    remaining = folding_groups(repo.snapshot().commands)
    assert remaining[ids[6]]['number'] == 1
    graph.close()
    table.close()
editor.close()
print('PASS: parsing, validation, editor, no-op execution, persistence, table/graph visibility, single/double click, loops and numbering')
