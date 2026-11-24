"""Keyboard triggers, clipboard placement, grouped drag and visible insertion markers."""
import os
import sys, json, sqlite3, tempfile
from pathlib import Path
from types import SimpleNamespace
from unittest.mock import patch
if __package__ in (None, ''):
    sys.path.insert(0, str(Path(__file__).resolve().parents[1]))
from anclicker.platform.qt_compat.QtWidgets import QApplication, QTableWidgetItem, QAbstractItemView
from anclicker.platform.qt_compat.QtCore import Qt, QPointF, QEvent, QMimeData
from anclicker.platform.qt_compat.QtGui import QKeyEvent, QMouseEvent
from anclicker.instructions.registry import get_instruction_spec
from anclicker.domain.instructions import InstructionDraft, CommandRecord, ExecutionContext
from anclicker.storage.graph_repository import GraphRepository
from anclicker.domain.step_folding import folding_groups
from anclicker.ui.instruction_table import InstructionTableWidget, InstructionTableController
from anclicker.execution.instruction_helpers.window_trigger_wait import wait_for_trigger
from pynput import keyboard

os.environ.setdefault('QT_QPA_PLATFORM', 'offscreen')
app = QApplication.instance() or QApplication([])
for kind in ('中键激活', '窗口中键激活'):
    spec = get_instruction_spec(kind)
    editor = spec.create_editor()
    editor.operation.setCurrentText('任意键盘按键')
    draft = editor.get_draft()
    assert draft.type_id == kind and draft.parameters == {'触发按键': '任意键盘按键'}
    editor.load_draft(draft)
    assert editor.get_draft() == draft
    with patch('anclicker.instructions.' + ('键鼠' if kind == '中键激活' else '窗口键鼠') + '.' + kind + '.executor.wait_for_trigger', return_value=True) as wait:
        assert spec.create_executor().execute_once(ExecutionContext(), CommandRecord(1, kind, draft.parameters)) is True
        wait.assert_called_once()
    editor.close()

class KeyListener:
    def __init__(self, **callbacks): self.callbacks, self.stopped = callbacks, False
    def start(self): self.callbacks['on_press'](SimpleNamespace(vk=65))
    def is_alive(self): return True
    def stop(self): self.stopped = True
    def join(self, **kwargs): pass
with patch.object(keyboard, 'Listener', KeyListener):
    assert wait_for_trigger(ExecutionContext(), {'触发按键': '任意键盘按键'})
    assert not wait_for_trigger(ExecutionContext(stop_requested=True), {'触发按键': '任意键盘按键'})
print('PASS both trigger editors, any-key execution and cancellation')

class Host(SimpleNamespace): pass
class DropEvent:
    def __init__(self, table, mime, y): self.table, self.mime, self.y, self.accepted = table, mime, y, False
    def position(self): return QPointF(20, self.y)
    def mimeData(self): return self.mime
    def source(self): return self.table
    def acceptProposedAction(self): self.accepted = True
    def ignore(self): self.accepted = False

def key(table, code):
    app.sendEvent(table, QKeyEvent(QEvent.KeyPress, code, Qt.ControlModifier))

with tempfile.TemporaryDirectory() as folder:
    dbpath = Path(folder) / 'project.db'
    with sqlite3.connect(dbpath) as db: GraphRepository.initialize_schema(db)
    db.close()
    repo = GraphRepository(str(dbpath))
    ids = repo.append_recording([InstructionDraft('时间等待', {'时长': 0}, note=str(i)) for i in range(6)])
    table = InstructionTableWidget(0, 7)
    table.setSelectionMode(QAbstractItemView.ExtendedSelection)
    table.resize(840, 370)
    messages = []
    def refresh(*args):
        commands = repo.list_commands()
        table.setRowCount(len(commands))
        for row, command in enumerate(commands):
            for col in range(7):
                item = QTableWidgetItem(command.type_id if col == 2 else str(row + 1))
                item.setData(Qt.UserRole, command.id)
                table.setItem(row, col, item)
        table.update_comment_ranges(repo.snapshot())
    host = Host(repository=repo, reload_graph=refresh, graphFinalized=Host(emit=lambda *a: None))
    workspace = Host(window=Host(workspace=host, statusBar=Host(showMessage=lambda message, *a: messages.append(message))),
                     command_table=table, _table_mutation_allowed=lambda: True)
    controller = InstructionTableController(workspace)
    workspace._select_table_ids = controller._select_table_ids
    table.copyRequested.connect(controller.copy_table_commands)
    table.pasteRequested.connect(controller.paste_table_commands)
    table.rowsMoved.connect(controller.move_table_commands)
    refresh(); table.show(); app.processEvents()
    table.setCurrentCell(1, 2)
    key(table, Qt.Key_C)
    assert '第 2 行' in messages[-1]
    table.setCurrentCell(3, 2)
    key(table, Qt.Key_V)
    copied = table.selected_command_ids()
    assert len(copied) == 1, (copied, messages)
    assert [c.id for c in repo.list_commands()][4] == copied[0]
    assert len(table.selectedIndexes()) == 7 and '第 5 行' in messages[-1]
    table.clearSelection(); key(table, Qt.Key_V)
    assert repo.list_commands()[-1].id in table.selected_command_ids()
    assert '第 8 行' in messages[-1]
    # Locked destination inserts after every group member; unlocked inserts after the actual row.
    repo.update_command(ids[1], InstructionDraft('折叠步骤', {'下方条数': 2, '整体锁定': True, '已折叠': False}))
    refresh(); table.clearSelection(); table.setCurrentCell(2, 2); key(table, Qt.Key_V)
    pasted = table.selected_command_ids()[0]
    ordered = [c.id for c in repo.list_commands()]
    assert ordered.index(pasted) == ordered.index(ids[3]) + 1, (ordered, pasted, messages, table.selected_command_ids())
    assert folding_groups(repo.list_commands())[ids[1]]['members'] == set(ids[2:4])
    repo.set_step_locks([ids[1]], False)
    refresh(); table.clearSelection(); table.setCurrentCell(2, 2); key(table, Qt.Key_V)
    assert repo.list_commands()[3].id in table.selected_command_ids()
    print('PASS actual Ctrl+C/V, insertion after selected row or locked group, append and full-row selection with row numbers')
    # Ctrl-drag keeps a non-contiguous selection and sends every selected ID.
    selection = [ids[0], ids[-1]]
    controller._select_table_ids(selection)
    point = table.visualRect(table.model().index(0, 2)).center()
    captured = []
    class Drag:
        def __init__(self, parent): pass
        def setMimeData(self, mime): self.mime = mime
        def exec(self, action):
            captured.extend(json.loads(bytes(self.mime.data(table.ROW_MIME))))
            event = DropEvent(table, self.mime, table.viewport().height() + 10)
            table.dropEvent(event)
            assert event.accepted
    before = [c.id for c in repo.list_commands()]
    with patch('anclicker.ui.instruction_table.QDrag', Drag):
        table.mousePressEvent(QMouseEvent(QEvent.MouseButtonPress, QPointF(point), Qt.LeftButton, Qt.LeftButton, Qt.ControlModifier))
        table.mouseMoveEvent(QMouseEvent(QEvent.MouseMove, QPointF(point.x()+30, point.y()+25), Qt.NoButton, Qt.LeftButton, Qt.ControlModifier))
    assert captured == selection
    assert [c.id for c in repo.list_commands()] == [i for i in before if i not in selection] + selection
    assert set(table.selected_command_ids()) == set(selection)
    # Dragging a member of a locked group moves the entire group.
    repo.set_step_locks([ids[1]], True); refresh()
    group = {ids[1]} | folding_groups(repo.list_commands())[ids[1]]['members']
    controller.move_table_commands([ids[2]], table.rowCount())
    assert set(table.selected_command_ids()) == group
    assert set(c.id for c in repo.list_commands()[-len(group):]) == group
    print('PASS multi-row Ctrl drag ordering, retained selection and whole locked group moves')
    mime = QMimeData(); mime.setData(table.ROW_MIME, json.dumps(selection).encode())
    for y in (-100, table.viewport().height() + 100):
        table._show_drop_line(DropEvent(table, mime, y))
        assert table.viewport().rect().contains(table._drop_line.geometry())
    table._show_drop_line(DropEvent(table, mime, table.rowViewportPosition(1)+table.rowHeight(1)-2))
    app.processEvents()
    pixels = table._drop_line.grab().toImage()
    red = blue = 0
    for y in range(pixels.height()):
        for x in range(pixels.width()):
            color = pixels.pixelColor(x, y)
            red += color.red() > 200 and color.green() < 120 and color.blue() < 120
            blue += color.blue() > 150 and color.red() < 150
    assert red > 20 and blue > 100
    output = Path('artifacts/validation/requested-interactions'); output.mkdir(parents=True, exist_ok=True)
    table.grab().save(str(output / 'table-marker.png'))
    table.close(); app.clipboard().clear(); app.processEvents()
    print('PASS red inward arrows, blue line and viewport clipping; screenshot saved')
