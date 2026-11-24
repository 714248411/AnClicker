"""Palette MIME safety, nearest visible gaps and stable parameter-dialog insertion."""
import os
os.environ.setdefault('QT_QPA_PLATFORM', 'offscreen')
import sys
from pathlib import Path
sys.path.insert(0, str(Path(__file__).resolve().parents[1]))
import sqlite3
import tempfile
from types import SimpleNamespace, MethodType
from unittest.mock import patch
from anclicker.platform.qt_compat.QtCore import Qt, QPointF, QMimeData
from anclicker.platform.qt_compat.QtWidgets import QApplication, QTableWidgetItem, QTreeWidgetItem, QTableWidget
from anclicker.ui.instruction_table import InstructionTableWidget, InstructionTableController
from anclicker.ui.instruction_workspace import InstructionWorkspace
from anclicker.ui.node_editor.palette import _InstructionTree, INSTRUCTION_MIME_TYPE, TYPE_ID_ROLE
from anclicker.instructions.registry import INSTRUCTION_SPECS
from anclicker.domain.instructions import InstructionDraft
from anclicker.storage.graph_repository import GraphRepository

app = QApplication.instance() or QApplication([])
class Event:
    def __init__(self, x, y, mime, source=None):
        self.point, self.mime, self.origin = QPointF(x, y), mime, source
        self.accepted = False
    def position(self): return self.point
    def mimeData(self): return self.mime
    def source(self): return self.origin
    def acceptProposedAction(self): self.accepted = True
    def ignore(self): self.accepted = False
    def accept(self): self.accepted = True

class Workspace(SimpleNamespace): pass
with tempfile.TemporaryDirectory() as folder:
    dbpath = Path(folder) / 'drop.db'
    with sqlite3.connect(dbpath) as db:
        GraphRepository.initialize_schema(db)
    db.close()
    repo = GraphRepository(str(dbpath))
    ids = repo.append_recording([InstructionDraft('折叠步骤', {'下方条数': 2})] +
                               [InstructionDraft('时间等待', {'时长': 0}) for _ in range(3)])
    table = InstructionTableWidget(0, 7)
    table.resize(950, 450)
    table.verticalHeader().setDefaultSectionSize(40)
    workspace = Workspace(command_table=table, table_state=SimpleNamespace(setText=lambda _: None),
                          theme_mode='light', running_command_id=None)
    controller = InstructionTableController(workspace)
    workspace._current_graph_state = lambda: (repo.snapshot(), None)
    workspace._apply_comment_row_colors = controller._apply_comment_row_colors
    workspace.highlight_running_command = lambda *a, **k: None
    def refresh(): controller.refresh_table(); app.processEvents()
    refresh()
    table.show(); app.processEvents()
    emitted = []
    table.instructionDropped.connect(lambda kind, before: emitted.append((kind, before)))
    mime = QMimeData(); mime.setData(INSTRUCTION_MIME_TYPE, '折叠步骤'.encode())
    top = table.rowViewportPosition(0)
    bottom = top + table.rowHeight(0)
    for column in range(7):
        x = table.columnViewportPosition(column) + 5
        event = Event(x, top+2, mime)
        table.dragEnterEvent(event)
        assert event.accepted and not table._drop_line.isHidden()
        table.dragMoveEvent(event)
        assert table._drop_row(event) == 0
        table.dropEvent(event)
        assert emitted[-1] == ('折叠步骤', ids[0])
        assert table.item(0, 0).text() == '1', 'Drop must never overwrite the sequence cell'
        assert table._drop_line.isHidden()
    # Bottom of a collapsed opener is the boundary after all hidden children.
    event = Event(10, bottom-2, mime)
    table.dragMoveEvent(event)
    assert table._drop_row(event) == 3
    assert abs(table._drop_line.y()+table._drop_line.height()//2-bottom) <= 1
    assert table.viewport().rect().contains(table._drop_line.geometry())
    table.dropEvent(event)
    assert emitted[-1] == ('折叠步骤', ids[3])
    # Invalid column / right blank area still uses the pointer Y coordinate.
    event = Event(5000, top+2, mime)
    assert table._drop_row(event) == 0
    event = Event(10, table.viewport().height()-5, mime)
    table.dropEvent(event)
    assert emitted[-1] == ('折叠步骤', 'end')
    # Reject Qt native item-model MIME: this used to fall through to cell overwrite.
    native = QTableWidget(1, 1)
    native.setItem(0, 0, QTableWidgetItem('折叠步骤'))
    raw = native.mimeData([native.item(0, 0)])
    event = Event(10, top+2, raw)
    before = [[table.item(r,c).text() for c in range(7)] for r in range(table.rowCount())]
    table.dragEnterEvent(event); assert not event.accepted
    table.dragMoveEvent(event); assert not event.accepted
    table.dropEvent(event); assert not event.accepted
    assert before == [[table.item(r,c).text() for c in range(7)] for r in range(table.rowCount())]
    # All registered instructions use the same safe MIME path.
    tree = _InstructionTree()
    class Drag:
        def __init__(self, parent): pass
        def setMimeData(self, value): self.mime = value
        def exec(self, action):
            assert action == Qt.CopyAction
            event = Event(10, top+2, self.mime)
            assert table._type_id(event) == tree.instruction_type(tree.currentItem())
    with patch('anclicker.ui.node_editor.palette.QDrag', Drag):
        for spec in INSTRUCTION_SPECS:
            item = QTreeWidgetItem(tree, [spec.display_name])
            item.setData(0, TYPE_ID_ROLE, spec.type_id)
            tree.setCurrentItem(item)
            tree.startDrag(Qt.CopyAction | Qt.MoveAction)
    # Use the actual add-command commit with a deferred editor callback.
    callbacks, errors = [], []
    host = Workspace(repository=repo, parent_window=None,
        palette=SimpleNamespace(quick_parameters=lambda _: None, command_added=lambda *args: None),
        _check_parameter_save_allowed=lambda: None, reload_graph=lambda *_: refresh(),
        graphFinalized=SimpleNamespace(emit=lambda *_: refresh()), statusMessage=SimpleNamespace(emit=lambda *_: None),
        _editor_context=lambda: None, _connect_editor_test=lambda *args: None,
        _run_parameter_editor=lambda editor, callback, key: callbacks.append(callback),
        _show_error=lambda title, error: errors.append(error))
    host.add_command = MethodType(InstructionWorkspace.add_command, host)
    InstructionWorkspace.add_palette_command(host, '折叠步骤', before_command_id=ids[3])
    assert len(repo.list_commands()) == 4 and callbacks, 'No insertion before settings confirmation'
    # A separate insertion changes row indices while the first dialog stays open.
    extra = repo.insert_table_commands([InstructionDraft('时间等待', {'时长': 0})], before_command_id=ids[0])[0]
    new_id = callbacks.pop()(InstructionDraft('折叠步骤', {'下方条数': 1}))
    ordered = [c.id for c in repo.list_commands()]
    assert ordered == [extra, *ids[:3], new_id, ids[3]], ordered
    assert not errors
    assert [table.item(row, 0).text() for row in range(table.rowCount())] == [str(i+1) for i in range(len(ordered))]
    assert '折叠1' in table.item(1, 2).text()
    assert '折叠2' in table.item(4, 2).text()
    assert [c.id for c in repo.validate_graph().commands] == ordered
    # Deleted anchor must not silently append or partially insert.
    InstructionWorkspace.add_palette_command(host, '折叠步骤', before_command_id=ids[3])
    repo.delete_commands([ids[3]])
    before = repo.snapshot()
    try:
        callbacks.pop()(InstructionDraft('折叠步骤'))
    except Exception:
        pass
    else:
        raise AssertionError('Deleted insertion boundary accepted')
    assert repo.snapshot() == before
    # Empty table has one insertion boundary at the top.
    empty = InstructionTableWidget(0, 7)
    assert empty._drop_row(Event(10, 10, mime)) == 0
    table.close(); tree.close(); native.close(); empty.close()
print('PASS: all palette types, sequence-cell protection, every column, nearest edge, collapsed/empty/end boundaries, stable deferred insertion, numbering and missing-anchor rollback')
