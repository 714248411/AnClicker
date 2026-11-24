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
    viewhost.theme_mode = "dark"
    view = host.editor.view
    captured = []
    view.instructionCreateRequested.disconnect()
    view.instructionCreateRequested.connect(lambda *args: captured.append(args))
    event = QContextMenuEvent(QContextMenuEvent.Mouse, QPoint(400, 250), view.mapToGlobal(QPoint(400, 250)))
    def choose_create(left, right, position, owner):
        assert any(action.text() == '全选' for action in left.actions())
        assert right._instruction_submenus
        assert right._template_submenu.title() == '插入模板'
        animation = left._drag_animation_menu
        assert hasattr(animation, '_rounded_menu_background')
        assert animation.testAttribute(Qt.WA_TranslucentBackground)
        animation.show()
        app.processEvents()
        animation.grab().save('artifacts/validation/animation-submenu-dark.png')
        animation.hide()
        return next(action for sub in right._instruction_submenus for action in sub.actions() if action.text() == '时间等待')
    with patch.object(view, '_node_at', return_value=None), patch.object(view, 'itemAt', return_value=None), patch('anclicker.ui.node_editor.view.exec_two_column_menu', choose_create):
        view.contextMenuEvent(event)
    expected = view.mapToScene(event.pos())
    assert captured == [('时间等待', expected.x(), expected.y())]
    print('PASS graph two columns, categories, templates, themed animation submenu and creation coordinates')
    node = host.editor.scene.nodes_by_command_id[ids[1]]
    def choose_copy(left, right, position, owner):
        assert any(action.text() == '删除流程连接线' for action in right.actions())
        assert not any(action.text() == '删除流程连接线' for action in left.actions())
        return next(action for action in left.actions() if action.text() == '复制')
    copied = []
    view.copyRequested.disconnect()
    view.copyRequested.connect(copied.append)
    with patch.object(view, '_node_at', return_value=node), patch('anclicker.ui.node_editor.view.exec_two_column_menu', choose_copy):
        view.contextMenuEvent(event)
    assert copied == [[ids[1]]]
    print('PASS graph node operations and connection operations split without changing selection')
    window.close()
