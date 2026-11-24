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
        InstructionDraft('折叠步骤', {'下方条数':2, '整体锁定':True, '已折叠':True}),
        ordinary(), ordinary(), ordinary(), ordinary()])
    host.reload_graph(); refresh(); window.resize(1000,500); window.show(); app.processEvents()
    point = lambda row:QPoint(350, table.rowViewportPosition(row)+table.rowHeight(row)//2)
    event = DragEvent(point(0), table, [ids[-1]])
    table.dragEnterEvent(event)
    started = time.monotonic()
    # Repeated native drag moves at the same position must not restart dwell.
    while time.monotonic() - started < 4.8:
        table.dragMoveEvent(event); qwait(30)
    assert table.step_groups[ids[0]]['locked']
    assert table.step_groups[ids[0]]['collapsed']
    dwell(lambda:not table.step_groups[ids[0]]['locked'])
    assert time.monotonic() - started >= 4.98
    assert host.repository.get_command(ids[0]).parameters['整体锁定']
    assert table._drag_scope == [('step', ids[0])]
    table.dragLeaveEvent(event)
    assert table.step_groups[ids[0]]['locked'] and not table._temporary_unlocks
    print('PASS five-second dwell despite repeated moves, expansion after unlock, cancellation restores lock')

    table.dragEnterEvent(event)
    dwell(lambda:not table.step_groups[ids[0]]['locked'], 5300)
    drop = DragEvent(QPoint(350, table.rowViewportPosition(1)+1), table, [ids[-1]])
    table.dragMoveEvent(drop); table.dropEvent(drop)
    assert drop.accepted
    assert [c.id for c in host.repository.list_commands()] == [ids[0],ids[-1],ids[1],ids[2],ids[3]]
    group = table.step_groups[ids[0]]
    assert group['locked'] and {ids[-1],ids[1],ids[2]} <= group['members']
    assert host.repository.get_command(ids[0]).parameters['整体锁定']
    print('PASS drop into temporary unlocked collection, members retained and lock restored atomically')

    # A deferred parameter editor keeps its permission, never a persisted unlock.
    table._drop_unlocks = {ids[0]}
    callbacks = []
    with patch.object(host, '_run_parameter_editor', side_effect=lambda editor, callback, key:callbacks.append(callback)):
        host.add_command('时间等待', before_command_id=ids[1])
    assert callbacks and host.repository.get_command(ids[0]).parameters['整体锁定']
    inserted = callbacks[0](ordinary())
    assert inserted in table.step_groups[ids[0]]['members']
    assert table.step_groups[ids[0]]['locked']
    assert host.repository.get_command(ids[0]).parameters['整体锁定']
    before = host.repository.list_commands()
    try:
        host.repository.reorder_table_commands([ids[0]], temporary_unlocks={ids[0]})
    except Exception:
        pass
    else:
        raise AssertionError('Invalid reorder accepted')
    assert host.repository.list_commands() == before
    assert host.repository.get_command(ids[0]).parameters['整体锁定']
    print('PASS deferred palette insert and rejected transaction retain lock')
    # A drag beginning inside a locked source must wait five seconds to leave it.
    source = ids[1]
    outside = QPoint(350, table.rowViewportPosition(table.rowCount()-1)+table.rowHeight(table.rowCount()-1)-2)
    event = DragEvent(outside, table, [source])
    table.dragEnterEvent(event); qwait(2100)
    assert table._drag_scope == [('step', ids[0])]
    assert .38 < table.lock_progress(ids[0]) < .48
    table.dropEvent(event)
    assert not event.accepted and host.repository.list_commands() == before
    assert table.lock_progress(ids[0]) is None
    table.dragEnterEvent(event); qwait(3000)
    assert .55 < table.lock_progress(ids[0]) < .7
    table.grab().save(str(artifacts/'lock-progress.png'))
    dwell(lambda:not table._drag_scope, 2300)
    assert not table.step_groups[ids[0]]['locked']
    assert table.lock_progress(ids[0]) is None
    table.dropEvent(event)
    assert event.accepted
    assert host.repository.list_commands()[-1].id == source
    assert source not in table.step_groups[ids[0]]['members']
    assert table.step_groups[ids[0]]['locked']
    print('PASS outward 5s lock progress, early-drop rejection, selected member exit and restored lock')
    QApplication.clipboard().clear(); window.close(); window.deleteLater(); qwait(30)
print('PASS automatic drag unlock suite')
