"""Real Qt dwell timers, committed edits, cancellation and animation isolation."""
import os
import sys
import tempfile
import json
import time
from pathlib import Path
from types import SimpleNamespace
from unittest.mock import patch
if __package__ in (None, ''):
    sys.path.insert(0, str(Path(__file__).resolve().parents[1]))
from anclicker.platform.qt_compat.QtWidgets import QApplication, QWidget, QVBoxLayout, QTableWidgetItem, QMenu, QDockWidget, QMessageBox
from anclicker.platform.qt_compat.QtCore import Qt, QPoint, QPointF, QRectF, QMimeData, QTimer
from anclicker.platform.qt_compat.QtGui import QFont, QFontDatabase
from anclicker.instructions.registry import INSTRUCTION_SPECS
from anclicker.platform.qt_compat.QtGui import QContextMenuEvent
from anclicker.domain.instructions import InstructionDraft
from anclicker.storage.database import DatabaseOperation
from anclicker.ui.instruction_workspace import InstructionWorkspace
from anclicker.ui.instruction_table import InstructionTableWidget, InstructionTableController, command_indent_width
from anclicker.ui.drag_feedback import animation_policy, animation_menu, feedback_call
from anclicker.ui.node_editor.palette import INSTRUCTION_MIME_TYPE

os.environ.setdefault('QT_QPA_PLATFORM', 'offscreen')
app = QApplication.instance() or QApplication([])
font_id = QFontDatabase.addApplicationFont('C:/Windows/Fonts/msyh.ttc')
families = QFontDatabase.applicationFontFamilies(font_id)
if families:
    app.setFont(QFont(families[0], 10))
artifacts = Path('artifacts/validation/drag-animations'); artifacts.mkdir(parents=True, exist_ok=True)
class ViewHost(SimpleNamespace):
    pass
class DragEvent:
    def __init__(self, point, source=None, ids=None):
        self.point = QPointF(point); self.owner = source; self.accepted = False
        self.mime = QMimeData()
        if ids is None:
            self.mime.setData(INSTRUCTION_MIME_TYPE, '时间等待'.encode('utf-8'))
        else:
            self.mime.setData(InstructionTableWidget.ROW_MIME, json.dumps(ids).encode('ascii'))
    def position(self): return self.point
    def mimeData(self): return self.mime
    def source(self): return self.owner
    def acceptProposedAction(self): self.accepted = True
    def accept(self): self.accepted = True
    def ignore(self): self.accepted = False

def qwait(milliseconds):
    end = time.monotonic()+milliseconds/1000
    while time.monotonic()<end:
        app.processEvents(); time.sleep(.005)

def dwell(check, milliseconds=2200):
    end = time.monotonic() + milliseconds/1000
    while time.monotonic() < end and not check():
        qwait(10)
    assert check(), 'Dwell did not expand target'

with tempfile.TemporaryDirectory() as folder:
    window = QWidget(); window.db = DatabaseOperation(str(Path(folder)/'test.db'))
    window.workspace = host = InstructionWorkspace(window.db.db_path, window)
    table = InstructionTableWidget(0, 7, window)
    table.setColumnWidth(2, 300); table.setHorizontalHeaderLabels(['行','编号','指令','参数','重复','异常','备注'])
    layout = QVBoxLayout(window); layout.addWidget(table); layout.addWidget(host.editor)
    host.editor.hide()
    def refresh(*args):
        commands = host.repository.list_commands(); table.setRowCount(len(commands))
        for row, command in enumerate(commands):
            for col in range(7):
                text = command.type_id if col == 2 else command.note if col == 6 else str(row+1)
                item = QTableWidgetItem(text); item.setData(Qt.UserRole, command.id); item.setToolTip(text)
                table.setItem(row, col, item)
        table.update_comment_ranges(host.repository.snapshot())
    viewhost = ViewHost(window=window, command_table=table, refresh_table=refresh, _table_mutation_allowed=lambda:True)
    window.view_workspace = viewhost
    window.statusBar = SimpleNamespace(showMessage=lambda *args:None)
    controller = InstructionTableController(viewhost)
    viewhost._select_table_ids = controller._select_table_ids
    host.graphFinalized.connect(refresh)
    table.hoverExpandRequested.connect(host.expand_step_for_drag)
    table.rowsMoved.connect(lambda ids, boundary: controller.move_table_commands(ids, boundary))
    table.instructionDropped.connect(lambda kind, before: host.add_command(kind, configure=False, before_command_id=before))
    table.cutRequested.connect(lambda:host.cut_commands(table.selected_command_ids()))
    ordinary = lambda:InstructionDraft('时间等待', {'时长':0})
    ids = host.repository.append_recording([
        InstructionDraft('折叠步骤', {'下方条数':2, '整体锁定':True, '已折叠':False}),
        ordinary(), ordinary(), ordinary()])
    host.reload_graph(); refresh(); window.resize(1000,500); window.show(); app.processEvents()
    table.instruction_specs_provider = lambda: host.editor.view._instruction_specs
    point = QPoint(table.columnViewportPosition(3)+8, table.rowViewportPosition(1)+10)
    event = QContextMenuEvent(QContextMenuEvent.Mouse, point, table.viewport().mapToGlobal(point))
    def choose_instruction(left, menu, position, owner):
        categories = [sub.title() for sub in menu._instruction_submenus]
        assert categories == list(dict.fromkeys(spec.category for spec in host.editor.view._instruction_specs.values()))
        assert any('第 2 行上方' in action.text() for action in menu.actions())
        return next(action for sub in menu._instruction_submenus for action in sub.actions() if action.text() == '时间等待')
    before = host.repository.list_commands()
    with patch('anclicker.ui.instruction_table.exec_two_column_menu', choose_instruction), patch.object(QMessageBox, 'question', return_value=QMessageBox.No) as ask:
        table.contextMenuEvent(event)
        assert ask.call_count == 1
    assert host.repository.list_commands() == before
    with patch('anclicker.ui.instruction_table.exec_two_column_menu', choose_instruction), patch.object(QMessageBox, 'question', return_value=QMessageBox.Yes) as ask:
        table.contextMenuEvent(event)
        assert ask.call_count == 1
    commands = host.repository.list_commands()
    new_id = next(c.id for c in commands if c.id not in ids)
    assert commands[1].id == new_id and commands[2].id == ids[1]
    assert new_id in table.step_groups[ids[0]]['members'] and table.step_groups[ids[0]]['locked']
    assert host.repository.get_command(ids[0]).parameters['整体锁定']
    with patch.object(QMessageBox, 'question') as ask:
        table._insert_menu_command('时间等待', 'end')
        assert not ask.called
    assert host.repository.list_commands()[-1].id not in ids + [new_id]
    print('PASS actual parameter-cell context menu, shared categories, cancel/confirm locked insertion and empty-area append')

    table.hide(); host.editor.show(); app.processEvents()
    view = host.editor.view
    transform = view.transform(); scroll = (view.horizontalScrollBar().value(), view.verticalScrollBar().value())
    dropped = host.add_command('时间等待', x=1234.5, y=-456.25, configure=False)
    node = host.editor.scene.nodes_by_command_id[dropped]
    assert (node.x(),node.y()) == (1234.5,-456.25)
    persisted = next(n for n in host.repository.snapshot().nodes if n.command_id == dropped)
    assert (persisted.x,persisted.y) == (1234.5,-456.25)
    assert view.transform() == transform
    assert (view.horizontalScrollBar().value(),view.verticalScrollBar().value()) == scroll
    host.reload_graph()
    node = host.editor.scene.nodes_by_command_id[dropped]
    assert (node.x(),node.y()) == (1234.5,-456.25)
    callbacks = []
    with patch.object(host, '_run_parameter_editor', side_effect=lambda editor, callback, key:callbacks.append(callback)):
        host.add_command('时间等待', x=-345.5, y=678.25)
    deferred = callbacks[0](ordinary())
    node = host.editor.scene.nodes_by_command_id[deferred]
    assert (node.x(),node.y()) == (-345.5,678.25)
    host.arrangement.rearrange()
    node = host.editor.scene.nodes_by_command_id[deferred]
    assert (node.x(),node.y()) != (-345.5,678.25)
    print('PASS precise graph drop coordinates, persistence, unchanged view, deferred editor and manual rearrange')
    QApplication.clipboard().clear(); window.close(); window.deleteLater(); qwait(30)
print('PASS table insertion and graph drop suite')
