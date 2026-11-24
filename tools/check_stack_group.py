"""Stacked locked groups, any-member dragging, cancellation and one-row menus."""
import os
os.environ.setdefault('QT_QPA_PLATFORM', 'offscreen')
import sys
from pathlib import Path
sys.path.insert(0, str(Path(__file__).resolve().parents[1]))
import sqlite3
import tempfile
from types import SimpleNamespace, MethodType
from unittest.mock import patch
from anclicker.domain.instructions import InstructionDraft
from anclicker.domain.step_folding import folding_groups
from anclicker.storage.graph_repository import GraphRepository
from anclicker.instructions.registry import INSTRUCTION_SPECS
from anclicker.ui.instruction_workspace import InstructionWorkspace
from anclicker.ui.instruction_table import InstructionTableWidget
from anclicker.ui.node_editor.widget import NodeEditorWidget
from anclicker.platform.qt_compat.QtWidgets import QApplication, QTableWidgetItem, QMenu
from anclicker.platform.qt_compat.QtCore import Qt, QPointF
from anclicker.platform.qt_compat.QtGui import QContextMenuEvent
from PySide2.QtTest import QTest

app = QApplication.instance() or QApplication([])
class Host(SimpleNamespace): pass
class Press:
    def __init__(self, point): self.point = QPointF(point)
    def button(self): return Qt.LeftButton
    def modifiers(self): return Qt.NoModifier
    def position(self): return self.point

with tempfile.TemporaryDirectory() as folder:
    path = Path(folder) / 'stack.db'
    with sqlite3.connect(path) as db:
        GraphRepository.initialize_schema(db)
    db.close()
    repo = GraphRepository(str(path))
    ids = repo.append_recording([InstructionDraft('时间等待', {'时长': 0}) for _ in range(4)])
    graph = NodeEditorWidget(); graph.resize(900, 600)
    table = InstructionTableWidget(0, 7); table.resize(900, 400)
    errors = []
    host = Host(repository=repo, editor=graph, _check_parameter_save_allowed=lambda: None,
                _show_error=lambda title, error: errors.append(error), graphFinalized=SimpleNamespace(emit=lambda *_: None))
    def reload(*args):
        snapshot = repo.snapshot()
        graph.load_graph(snapshot.nodes, snapshot.edges, INSTRUCTION_SPECS, allow_incomplete=True)
        InstructionWorkspace._apply_step_folds(host, snapshot)
        table.setRowCount(len(snapshot.commands))
        for row, command in enumerate(snapshot.commands):
            for col in range(7):
                item = QTableWidgetItem(command.type_id if col == 2 else str(row+1))
                item.setData(Qt.UserRole, command.id); item.setToolTip(item.text()); table.setItem(row, col, item)
        table.update_comment_ranges(snapshot)
    host.reload_graph = reload
    host.set_step_locks = MethodType(InstructionWorkspace.set_step_locks, host)
    reload(); graph.show(); table.show(); app.processEvents()
    graph.scene.stepLocksRequested.connect(lambda selected, locked: host.set_step_locks(selected, locked))
    table.stepLocksRequested.connect(lambda selected, locked: host.set_step_locks(selected, locked))
    graph.scene.positionsCommitted.connect(lambda positions: repo.save_node_positions(positions))
    # Box-selected ordinary rows can be grouped by a single stateful menu action.
    table.selectRow(1)
    table.setSelectionMode(table.ExtendedSelection)
    for col in range(7): table.item(2, col).setSelected(True)
    def choose(expected):
        def execute(menu, *args):
            locks = [a for a in menu.actions() if a.text() in ('折叠加锁', '解锁')]
            assert len(locks) == 1 and locks[0].text() == expected
            locks[0].trigger()
            return locks[0]
        return execute
    point = table.visualItemRect(table.item(1,2)).center()
    with patch('anclicker.ui.instruction_table.exec_two_column_menu', choose('折叠加锁')):
        table.contextMenuEvent(QContextMenuEvent(QContextMenuEvent.Mouse, point, table.viewport().mapToGlobal(point)))
    assert not errors, errors
    commands = repo.list_commands()
    marker = next(c for c in commands if c.type_id == '折叠步骤')
    assert marker.parameters['整体锁定']
    assert folding_groups(commands)[marker.id]['members'] == {ids[1], ids[2]}
    group_ids = [marker.id, ids[1], ids[2]]
    source = {n.command_id: QPointF(n.x,n.y) for n in repo.snapshot().nodes if n.command_id is not None}
    scene, view = graph.scene, graph.view
    for index, cid in enumerate(group_ids):
        node = scene.nodes_by_command_id[cid]
        assert node.isVisible()
        if index:
            previous = scene.nodes_by_command_id[group_ids[index - 1]]
            assert node.pos() == previous.pos() + QPointF(previous.width - 8, -node.height - (22 if node.note else -8))
            assert node.zValue() > previous.zValue()
    for edge in scene.edges:
        if edge.source_node.command_id in group_ids and edge.target_node.command_id in group_ids:
            assert not edge.isVisible()
    # Higher cards must not cover the title or details of any earlier card.
    from anclicker.platform.qt_compat.QtCore import QRectF
    for index, cid in enumerate(group_ids):
        card = scene.nodes_by_command_id[cid]
        text_rect = card.mapRectToScene(QRectF(10, 14, card.width - 20, card.height - 14))
        for upper_id in group_ids[index + 1:]:
            upper = scene.nodes_by_command_id[upper_id]
            assert not upper.mapRectToScene(QRectF(0, 0, upper.width, upper.height + (20 if upper.note else 0))).intersects(text_rect)
    # Every stacked card exposes both connection ports, not just the front card.
    for cid in group_ids:
        card = scene.nodes_by_command_id[cid]
        for port in (card.input_port, card.output_port):
            view._set_zoom(1); view.centerOn(port.scenePos()); app.processEvents()
            assert view.itemAt(view.mapFromScene(port.scenePos())) is port
    # Real viewport events: locked cards keep input/output ports and side hotspots.
    node = scene.nodes_by_command_id[marker.id]
    outside = scene.nodes_by_command_id[ids[0]]
    scene._updating_graph = True
    outside.setPos(node.pos() + QPointF(-300, -180))
    scene._updating_graph = False
    links = []
    scene.connectionRequested.connect(lambda a, b: links.append((a, b)))
    for port, local in ((node.input_port, node.input_port.pos()),
                        (node.output_port, node.output_port.pos()),
                        (node.input_port, QPointF(node.width * .1, node.height * .5)),
                        (node.output_port, QPointF(node.width * .9, node.height * .5))):
        view._set_zoom(1)
        view.centerOn(node); app.processEvents()
        point = view.mapFromScene(node.mapToScene(local))
        before = {key: QPointF(scene.nodes_by_command_id[key].pos()) for key in group_ids}
        assert not view._begin_copy_drag(Press(point))
        QTest.mousePress(view.viewport(), Qt.LeftButton, Qt.NoModifier, point)
        assert scene._connection_port is port
        assert view._group_drag is None
        target = view.mapFromScene(outside.mapToScene(QPointF(outside.width / 2, outside.height / 2)))
        QTest.mouseRelease(view.viewport(), Qt.LeftButton, Qt.NoModifier, target)
        expected = (node.node_id, outside.node_id) if port.direction == 'output' else (outside.node_id, node.node_id)
        assert links[-1] == expected
        assert scene._connection_port is None
        assert all(scene.nodes_by_command_id[key].pos() == before[key] for key in group_ids)
    scene._updating_graph = True
    outside.setPos(source[ids[0]])
    scene._updating_graph = False
    # Drag each exposed card in turn; persist a translation of original spread positions.
    total = QPointF()
    for cid in group_ids:
        node = scene.nodes_by_command_id[cid]
        view._set_zoom(1)
        hit = node.pos() + QPointF(node.width / 2, node.height-6)
        view.centerOn(hit); app.processEvents()
        point = view.mapFromScene(hit)
        assert view._begin_copy_drag(Press(point))
        before = {key: QPointF(scene.nodes_by_command_id[key].pos()) for key in group_ids}
        end = QPointF(point) + QPointF(40,30)
        view._move_copy_drag(end)
        view._finish_copy_drag()
        total += QPointF(40,30)
        for key in group_ids:
            assert scene.nodes_by_command_id[key].pos() == before[key] + QPointF(40,30)
        saved = {n.command_id: QPointF(n.x,n.y) for n in repo.snapshot().nodes if n.command_id is not None}
        for key in group_ids: assert saved[key] == source[key] + total
        assert saved[ids[0]] == source[ids[0]] and saved[ids[3]] == source[ids[3]]
    node = scene.nodes_by_command_id[marker.id]
    hit = node.pos() + QPointF(node.width/2,node.height/2)
    view.centerOn(hit); app.processEvents(); point = view.mapFromScene(hit)
    before = {key: QPointF(scene.nodes_by_command_id[key].pos()) for key in group_ids}
    snapshot = repo.snapshot()
    assert view._begin_copy_drag(Press(point))
    view._move_copy_drag(QPointF(point)+QPointF(90,50)); view._finish_copy_drag(cancel=True)
    assert repo.snapshot() == snapshot
    assert all(scene.nodes_by_command_id[key].pos() == before[key] for key in group_ids)
    # Graph right-click has exactly one action, now Unlock, and restores translated layout.
    scene.clearSelection(); node.setSelected(True)
    with patch('anclicker.ui.node_editor.view.exec_two_column_menu', choose('解锁')):
        view.contextMenuEvent(QContextMenuEvent(QContextMenuEvent.Mouse,point,view.viewport().mapToGlobal(point)))
    assert not errors, errors
    assert not repo.get_command(marker.id).parameters['整体锁定']
    assert not scene.locked_groups
    for key in group_ids: assert scene.nodes_by_command_id[key].pos() == source[key] + total
    # Reopen the graph menu: same one row changes back to Lock.
    node = scene.nodes_by_command_id[marker.id]
    view.centerOn(node); app.processEvents()
    point = view.mapFromScene(node.pos()+QPointF(node.width/2,node.height/2))
    scene.clearSelection(); node.setSelected(True)
    with patch('anclicker.ui.node_editor.view.exec_two_column_menu', choose('折叠加锁')):
        view.contextMenuEvent(QContextMenuEvent(QContextMenuEvent.Mouse,point,view.viewport().mapToGlobal(point)))
    assert repo.get_command(marker.id).parameters['整体锁定']
    assert GraphRepository(str(path)).get_command(marker.id).parameters['整体锁定']
    graph.close(); table.close()
print('PASS: table selection grouping, diagonal layout, any-member drag, delta persistence, cancellation, unlock layout and single-row stateful menus')
