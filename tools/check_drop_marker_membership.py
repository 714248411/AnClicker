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
from anclicker.domain.instructions import InstructionDraft
from anclicker.domain.step_folding import folding_groups
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
        InstructionDraft('折叠步骤', {'下方条数':2, '已折叠':False}),
        ordinary(), ordinary(), ordinary(), ordinary()])
    host.reload_graph(); refresh(); window.resize(1000,500); window.show(); app.processEvents()
    point = lambda row:QPoint(350, table.rowViewportPosition(row)+table.rowHeight(row)-2)
    event = DragEvent(point(0), table, [ids[-1]])
    table.dragEnterEvent(event)
    dwell(lambda:len(table._drag_scope)==1)
    event = DragEvent(point(2), table, [ids[-1]])
    table.dragMoveEvent(event)
    assert table._drop_preview == (3, {ids[0]})
    # Release coordinates must not silently replace the last displayed marker.
    drop = DragEvent(point(4), table, [ids[-1]])
    table.dropEvent(drop)
    assert [c.id for c in host.repository.list_commands()] == [ids[0],ids[1],ids[2],ids[-1],ids[3]]
    assert table.step_groups[ids[0]]['members'] == {ids[1],ids[2],ids[-1]}
    print('PASS unlocked collection tail insertion follows displayed marker, not release coordinates')

    # Exactly the same physical gap: only the indentation/ownership changes.
    event = DragEvent(point(3), table, [ids[-1]])
    table.dragEnterEvent(event)
    outside = DragEvent(QPoint(50,point(3).y()), table, [ids[-1]])
    table.dragMoveEvent(outside)
    dwell(lambda:not table._drag_scope)
    before = [c.id for c in host.repository.list_commands()]
    assert table._drop_preview == (4, set())
    table.dropEvent(outside)
    assert [c.id for c in host.repository.list_commands()] == before
    assert table.step_groups[ids[0]]['members'] == {ids[1],ids[2]}
    print('PASS same row gap with outer marker removes collection membership')

    # Palette insertion must also retain the explicit inner target.
    event = DragEvent(point(0))
    table.dragEnterEvent(event); dwell(lambda:len(table._drag_scope)==1)
    event = DragEvent(point(2)); table.dragMoveEvent(event)
    assert table._drop_preview == (3, {ids[0]})
    before_ids = {c.id for c in host.repository.list_commands()}
    table.dropEvent(event)
    created = {c.id for c in host.repository.list_commands()} - before_ids
    assert created and created <= table.step_groups[ids[0]]['members']
    assert ids[-1] not in table.step_groups[ids[0]]['members']
    print('PASS palette tail insertion obeys marker and leaves outside rows outside')
    nested_db = DatabaseOperation(str(Path(folder)/'nested-marker.db'))
    repo = type(host.repository)(nested_db.db_path)
    nested = repo.append_recording([
        InstructionDraft('折叠步骤', {'下方条数':3, '动态范围':True, '已折叠':False}),
        InstructionDraft('折叠步骤', {'下方条数':1, '已折叠':False}), ordinary(), ordinary(), ordinary()])
    added = repo.insert_table_commands([ordinary()], before_command_id=nested[3], member_targets={nested[0],nested[1]})
    groups = folding_groups(repo.list_commands())
    assert set(added) <= groups[nested[0]]['members'] & groups[nested[1]]['members']
    order = [c.id for c in repo.list_commands()]
    repo.reorder_table_commands(order, inserted_members=added, member_targets={nested[0]})
    groups = folding_groups(repo.list_commands())
    assert added[0] in groups[nested[0]]['members'] and added[0] not in groups[nested[1]]['members']
    assert [c.id for c in repo.list_commands()] == order
    assert folding_groups(type(repo)(nested_db.db_path).list_commands()) == groups
    print('PASS nested parent/child ownership, unchanged row gap and persistence')
    QApplication.clipboard().clear(); window.close(); window.deleteLater(); qwait(30)
print('PASS marker membership suite')
