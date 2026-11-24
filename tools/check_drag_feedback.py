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
        InstructionDraft('折叠步骤', {'下方条数':4, '已折叠':True}), ordinary(),
        InstructionDraft('折叠步骤', {'下方条数':1, '已折叠':True}), ordinary(), ordinary(), ordinary()])
    host.reload_graph(); refresh(); window.resize(1000,500); window.show(); app.processEvents()
    policy = animation_policy(table); policy.headless = False
    assert animation_policy(host.editor.view) is policy
    before_edges = host.repository.snapshot().edges
    point = lambda row:QPoint(150, table.rowViewportPosition(row)+table.rowHeight(row)//2)
    assert table._hover_target(QPoint(150,table.rowViewportPosition(0)+table.rowHeight(0)+2)) == ('step',ids[0])
    event = DragEvent(point(0), table, [ids[-1]])
    table.dragEnterEvent(event)
    assert event.accepted and table.hover_expand.timer.interval() == 2000
    root_left = table._drop_line.x()
    assert table._drop_boundary(point(0))[0] in (0, 5)
    started = time.monotonic(); qwait(1800)
    assert table.step_groups[ids[0]]['collapsed']
    dwell(lambda:not table.step_groups[ids[0]]['collapsed'])
    assert time.monotonic()-started >= 1.98
    assert not table.isRowHidden(2) and table.isRowHidden(3)
    indent = command_indent_width(table.fontMetrics(), 1)
    assert table._drop_line.x() == root_left + indent
    assert table._drop_boundary(point(2))[0] in (2, 4)
    assert any(e['kind']=='hover' for e in table.feedback.effects)
    table.grab().save(str(artifacts/'parent-expanded.png'))
    # A separate dwell is required for the nested child; leaving cancels it.
    event = DragEvent(point(2), table, [ids[-1]])
    table.dragMoveEvent(event); qwait(120)
    table.dragLeaveEvent(event)
    assert not table.hover_expand.timer.isActive()
    assert table.step_groups[ids[2]]['collapsed']
    table.dragEnterEvent(event)
    dwell(lambda:table._drag_scope == [('step', ids[0])])
    table.dragMoveEvent(event)
    dwell(lambda:not table.step_groups[ids[2]]['collapsed'])
    assert not table.isRowHidden(3)
    assert host.repository.snapshot().edges == before_edges
    assert [c.id for c in host.repository.list_commands()] == ids
    table.grab().save(str(artifacts/'child-expanded.png'))
    assert table._drag_scope == [('step', ids[0]), ('step', ids[2])]
    assert table._drop_line.x() == root_left + 2 * indent
    # Moving left requests one outward level after the same two-second dwell.
    outside = DragEvent(QPoint(100, point(3).y()), table, [ids[-1]])
    table.dragMoveEvent(outside); qwait(1800)
    assert len(table._drag_scope) == 2
    dwell(lambda:len(table._drag_scope) == 1)
    assert table._drop_line.x() == root_left + indent
    # Remaining stationary in the outer gutter must keep stepping outward.
    qwait(1800)
    assert len(table._drag_scope) == 1
    dwell(lambda:not table._drag_scope)
    assert table._drop_line.x() == root_left
    assert table._drop_boundary(point(3))[0] in (0, 5)
    assert not table.step_groups[ids[0]]['collapsed']
    assert not table.step_groups[ids[2]]['collapsed']
    # An open subtree still requires separate entry dwells for each level.
    table.dragMoveEvent(event); qwait(100)
    assert not table._drag_scope
    dwell(lambda:len(table._drag_scope) == 1)
    table.dragMoveEvent(event)
    dwell(lambda:len(table._drag_scope) == 2)
    assert table._drop_line.x() == root_left + 2 * indent
    assert table.viewport().rect().contains(table._drop_line.geometry())
    table.dragLeaveEvent(event)
    assert not table._drag_scope
    print('PASS scope indicator indentation, outward dwell, open-group entry and viewport clipping')
    print('PASS 2s parent/child dwell, leave cancellation, one-level expansion and unchanged graph/order')

    # Disabled transitions must not disable hover expansion or successful drops.
    policy.configure(enabled=False)
    host.repository.set_step_collapsed(ids[2], True); host.reload_graph(); refresh()
    table.dragEnterEvent(DragEvent(point(2), table, [ids[-1]]))
    dwell(lambda:table._drag_scope == [('step', ids[0])])
    table.dragMoveEvent(DragEvent(point(2), table, [ids[-1]]))
    dwell(lambda:not table.step_groups[ids[2]]['collapsed'])
    assert not table.feedback.effects
    event = DragEvent(QPoint(150, table.rowViewportPosition(3)+1), table, [ids[-1]])
    table.dragMoveEvent(event); table.dropEvent(event)
    assert event.accepted
    assert [c.id for c in host.repository.list_commands()].index(ids[-1]) == 3
    assert not table.feedback.effects
    print('PASS disabled animation preserves hover expansion and committed row move')

    policy.configure(enabled=True)
    # Exercise every gate, including an active update and a modal/blocking flag.
    rect = QRectF(20,20,250,38)
    for flag in ('headless','background_batch','forced_low_quality','blocking_operation'):
        setattr(policy,flag,True)
        assert not table.feedback.play('move',[rect],committed=True)
        setattr(policy,flag,False)
    window._update_preparing = True
    assert not table.feedback.play('move',[rect],committed=True)
    window._update_preparing = False
    assert not table.feedback.play('move',[rect])
    assert not table.feedback.play('copy',[rect],count=policy.batch_limit+1,committed=True)
    assert not table.feedback.play('create',[QRectF(-300,-300,10,10)],committed=True)
    policy.configure(skip_offscreen=False)
    assert table.feedback.play('create',[QRectF(-300,-300,10,10)],committed=True)
    table.feedback.cancel(); policy.configure(skip_offscreen=True)
    for kind in ('move','copy','link','create','indicator','delete','rebound','hover','expand'):
        table.feedback.cancel()
        snapshots = table.feedback.capture([rect]) if kind == 'delete' else ()
        assert table.feedback.play(kind, [] if snapshots else [rect], snapshots=snapshots, committed=True)
        app.processEvents()
        assert table.feedback.effects, kind
        table.grab().save(str(artifacts/(kind+'.png')))
    menu = QMenu(); animation_menu(menu,table)
    toggle = menu._drag_animation_menu.actions()[0]
    toggle.trigger()
    assert not policy.enabled and not table.feedback.effects
    toggle.trigger(); menu.deleteLater()
    assert json.loads(window.db.get_setting_value(policy.SETTING))['enabled']
    print('PASS all animation variants, gates, shared master switch and persisted options')

    # Cancellation and an exception must never undo an already committed edit.
    stable = [c.id for c in host.repository.list_commands()]
    table.feedback.play('copy',[rect],committed=True)
    table.verticalScrollBar().valueChanged.emit(1)
    assert not table.feedback.effects and [c.id for c in host.repository.list_commands()]==stable
    with patch.object(table, 'show_edit_feedback', side_effect=RuntimeError('visual failure')):
        feedback_call(host, 'edit_feedback', 'move', ids)
    assert [c.id for c in host.repository.list_commands()]==stable
    with patch.object(table.feedback, '_policy', SimpleNamespace(allows=lambda *a,**k:1/0)):
        table.feedback._advance()
    assert not table.feedback.effects
    # Ongoing timers and further model writes are not held until effects finish.
    fired = []; table.feedback.play('move',[rect],committed=True)
    QTimer.singleShot(0,lambda:fired.append(True))
    host.repository.update_command_note(ids[0], '动画中保存')
    app.processEvents(); assert fired and host.repository.get_command(ids[0]).note=='动画中保存'
    print('PASS scroll/exception cancellation, timer progress and saving during feedback')

    # In-place graph expansion must preserve the exact dragged graphics object.
    host.repository.set_step_collapsed(ids[0], True); host.reload_graph(); refresh()
    table.hide(); host.editor.show(); window.resize(1000,720); app.processEvents(); host.editor.view.fit_graph(); qwait(50)
    view = host.editor.view; scene = host.editor.scene
    dragged = scene.nodes_by_command_id[ids[-1]]
    scene.begin_node_drag(dragged)
    parent = scene.nodes_by_command_id[ids[0]]
    view._track_hover(view.mapFromScene(parent.sceneBoundingRect().center()))
    assert view.hover_expand.target == ids[0], (view.hover_expand.target, ids[0])
    dwell(lambda:not scene.step_groups[ids[0]]['collapsed'])
    assert scene._drag_node is dragged and scene.nodes_by_command_id[ids[-1]] is dragged
    with patch.object(view.feedback, 'play', wraps=view.feedback.play) as play:
        view._drag_feedback_started = False
        view._show_drag_preview()
        for _ in range(20): view._show_drag_preview()
        assert play.call_count == 1
        view.pulse_group({ids[0]}, 'hover')
        assert play.call_count == 1
        view.show_edit_feedback('move', [ids[-1]])
        assert play.call_count == 2 and play.call_args.kwargs.get('committed')
    view._drag_feedback_started = False
    scene._drag_node = None; view.hover_expand.cancel()
    print('PASS one drag-start fade, no repeated mid-drag feedback, one committed end fade')
    view.grab().save(str(artifacts/'graph-hover.png'))
    print('PASS graph dwell expansion retains live drag item and scene')
    host.editor.hide(); table.show(); refresh(); app.processEvents()

    # Cut stores a pasteable group, commits removal first and supports immediate paste.
    table.clearSelection(); table.selectRow(table.rowCount()-1)
    selected = table.selected_command_ids()
    assert host.cut_commands(selected) == len(selected)
    assert all(host.repository.get_command(cid) is None for cid in selected)
    assert QApplication.clipboard().mimeData().hasFormat('application/x-anclicker-commands')
    controller.paste_table_commands('end')
    assert len(host.repository.list_commands()) == len(ids)
    print('PASS cut removal and clipboard paste round trip')
    # Business commits must still succeed if a feedback entry point itself fails.
    errors = []
    with patch.object(host, 'edit_feedback', side_effect=RuntimeError('entry animation failed')), patch.object(host, '_show_error', side_effect=lambda *a:errors.append(a)):
        created = host.add_command('时间等待', configure=False, before_command_id='end')
    assert created is not None and host.repository.get_command(created) is not None and not errors
    with patch.object(host.repository, 'insert_table_commands', side_effect=ValueError('rejected insertion')), patch.object(host, 'edit_feedback') as feedback, patch.object(host, '_show_error', side_effect=lambda *a:errors.append(a)):
        assert host.add_command('时间等待', configure=False, before_command_id='end') is None
        feedback.assert_not_called()
    assert errors
    print('PASS success precedes feedback; rejected business operations never play arrival')
    # Locked thread cut includes the whole group; dissolution keeps its body.
    thread_ids = host.repository.append_recording([InstructionDraft('多线程启动', {'线程名称':'待剪切','入口编号':0}), ordinary()])
    host.reload_graph(); refresh()
    assert host.cut_commands([thread_ids[0]]) == 2
    controller.paste_table_commands('end')
    restored = [c for c in host.repository.list_commands() if c.type_id=='多线程启动'][-1]
    members = set(restored.parameters['线程分组成员'])
    assert members
    with patch('anclicker.ui.instruction_workspace.QMessageBox.question', return_value=QMessageBox.Cancel):
        assert host.dissolve_thread(restored.id) is False
    assert host.repository.get_command(restored.id) is not None
    assert host.dissolve_thread(restored.id, confirm=False)
    assert all(host.repository.get_command(cid) is not None for cid in members)
    print('PASS locked group cut, paste and dissolve/cancel retain expected steps')
    # Floating panels must retain the same master policy as the host window.
    dock = QDockWidget(window); detached = InstructionTableWidget(0,7); dock.setWidget(detached); dock.setFloating(True)
    assert animation_policy(detached) is policy
    dock.close(); dock.deleteLater()
    table.feedback.play('move',[rect],committed=True)
    window.close(); app.processEvents()
    assert not table.feedback.timer.isActive()
    print('PASS close immediately cancels feedback')
    QApplication.clipboard().clear()
    window.deleteLater(); qwait(50)
print('PASS drag animation suite')
