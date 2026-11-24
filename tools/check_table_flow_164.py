"""Regression checks for table insertion/reordering and Qt 5 canvas panning."""
import json
import os
from pathlib import Path
import sqlite3
import sys
import tempfile
from types import SimpleNamespace

if __package__ in (None, ''):
    sys.path.insert(0, str(Path(__file__).resolve().parents[1]))
from anclicker.domain.instructions import InstructionDraft
from anclicker.storage.graph_repository import GraphRepository, START_NODE_ID, END_NODE_ID
from anclicker.instructions.registry import INSTRUCTION_SPECS
from anclicker.platform.qt_compat import configure_application, BINDING
from anclicker.platform.qt_compat.QtCore import QEvent, QPoint, QPointF, Qt, QTimer, QMimeData
from anclicker.platform.qt_compat.QtGui import QMouseEvent, QFocusEvent, QContextMenuEvent, QDropEvent
from anclicker.platform.qt_compat.QtWidgets import QApplication, QMainWindow, QTableWidgetItem, QMenu
from anclicker.ui.instruction_table import InstructionTableWidget, InstructionTableController
from anclicker.ui.node_editor.widget import NodeEditorWidget


class TestWorkspace(SimpleNamespace):
    pass


def new_repo(path):
    with sqlite3.connect(path) as connection:
        GraphRepository.initialize_schema(connection)
    return GraphRepository(str(path))


def drafts(*labels):
    return [InstructionDraft('时间等待', {'类型': '时间等待', '时长': 0, '单位': '秒'}, note=label) for label in labels]


def assert_chain(repo, ids):
    snapshot = repo.snapshot()
    assert [c.id for c in snapshot.commands] == ids
    nodes = {n.command_id: n.node_id for n in snapshot.nodes if n.command_id is not None}
    chain = [START_NODE_ID, *(nodes[item] for item in ids), END_NODE_ID]
    assert {(e.source, e.target, e.kind) for e in snapshot.edges} == {(a,b,0) for a,b in zip(chain, chain[1:])}
    assert [c.id for c in repo.validate_graph().commands] == ids
    # Reload from disk; no UI-only ordering is accepted.
    assert [c.id for c in GraphRepository(repo.db_path).snapshot().commands] == ids


def check_repository(folder):
    repo = new_repo(folder/'recordings.db')
    first = repo.append_recording(drafts('A','B','C'))
    assert_chain(repo, first)
    reordered = [first[0], first[2], first[1]]
    assert repo.reorder_table_commands(reordered)
    assert_chain(repo, reordered)
    # A later recording is a separate path; moving one of its existing rows
    # into the first recording must also replace the old bypass edge.
    later = repo.append_recording(drafts('D','E'))
    reordered = [first[0], later[0], first[2], first[1], later[1]]
    assert repo.reorder_table_commands(reordered)
    assert_chain(repo, reordered)
    loose = repo.append_recording(drafts('copied'), connect=False)
    reordered = reordered[:2] + loose + reordered[2:]
    assert repo.reorder_table_commands(reordered)
    assert_chain(repo, reordered)
    pasted = repo.insert_table_commands(drafts('P1','P2'), before_command_id=reordered[1])
    reordered = reordered[:1] + pasted + reordered[1:]
    assert_chain(repo, reordered)
    head = repo.insert_table_commands(drafts('head'), before_command_id=reordered[0])
    tail = repo.insert_table_commands(drafts('tail'))
    assert_chain(repo, head+reordered+tail)
    before = repo.snapshot()
    try:
        repo.insert_table_commands(drafts('invalid'), before_command_id=-999)
    except Exception:
        pass
    else:
        raise AssertionError('deleted insertion anchor accepted')
    assert repo.snapshot() == before
    # Preserve non-sequential semantics and branch metadata.
    branch = new_repo(folder/'branch.db')
    condition = branch.add_command(InstructionDraft('条件判断', {}), unconnected=True)
    rows = branch.append_recording(drafts('yes','no'), connect=False)
    nodes = {n.command_id: n.node_id for n in branch.snapshot().nodes if n.command_id is not None}
    branch.connect_nodes(START_NODE_ID, nodes[condition.id])
    branch.connect_nodes(nodes[condition.id], nodes[rows[0]], kind=1)
    branch.connect_nodes(nodes[condition.id], nodes[rows[1]], kind=2)
    edges = branch.snapshot().edges
    assert not branch.reorder_table_commands([condition.id, rows[1], rows[0]])
    assert branch.snapshot().edges == edges
    branch.insert_table_commands(drafts('branch paste'), before_command_id=rows[1])
    assert branch.snapshot().edges == edges
    print('PASS repository: recorded row reordering, disjoint recordings, copied rows, paste boundaries, rollback, branch preservation')


def check_table(folder, app):
    repo = new_repo(folder/'table.db')
    original = repo.append_recording(drafts('A','B','C','D'))
    window = QMainWindow()
    table = InstructionTableWidget(0,7,window)
    window.setCentralWidget(table)
    window.resize(900,450)
    messages = []
    window.statusBar = SimpleNamespace(showMessage=lambda *args: messages.append(args))
    host = SimpleNamespace(repository=repo, graphFinalized=SimpleNamespace(emit=lambda *_: refresh()))
    window.workspace = host
    workspace = TestWorkspace(window=window,command_table=table)
    controller = InstructionTableController(workspace)
    workspace._table_mutation_allowed = lambda: True
    workspace._select_table_ids = controller._select_table_ids
    def refresh():
        records = repo.list_commands()
        table.setRowCount(len(records))
        for row, record in enumerate(records):
            for col, label in enumerate((str(row+1),str(record.id),record.type_id,json.dumps(record.parameters),str(record.repeat_count),record.error_policy,record.note)):
                item=QTableWidgetItem(label)
                item.setData(Qt.UserRole,record.id)
                table.setItem(row,col,item)
    host.reload_graph = lambda *_: refresh()
    table.copyRequested.connect(controller.copy_table_commands)
    table.pasteRequested.connect(controller.paste_table_commands)
    table.pasteRelativeRequested.connect(controller.paste_table_commands)
    table.rowsMoved.connect(controller.move_table_commands)
    refresh(); window.show(); app.processEvents()
    table.selectRow(0); controller.copy_table_commands()
    table.clearSelection(); table.selectRow(1)
    # Exercise the actual context menu action, not only its controller method.
    def trigger_menu():
        menu=app.activePopupWidget()
        from anclicker.ui.two_column_menu import TwoColumnMenu
        assert isinstance(menu,TwoColumnMenu)
        action=next(a for a in menu.columns[0].actions() if a.text()=='粘贴指令到选择上方')
        assert action.isEnabled()
        action.trigger(); menu.close()
    QTimer.singleShot(0,trigger_menu)
    point=table.visualItemRect(table.item(1,2)).center()
    event=QContextMenuEvent(QContextMenuEvent.Mouse,point,table.viewport().mapToGlobal(point))
    table.contextMenuEvent(event)
    ids=[c.id for c in repo.list_commands()]
    assert ids[0]==original[0] and ids[2:]==original[1:]
    assert_chain(repo,ids)
    # Multi-cell and multi-row selection uses the top/bottom selected boundaries.
    table.clearSelection()
    table.item(1,2).setSelected(True);table.item(2,3).setSelected(True)
    controller.paste_table_commands('below')
    ordered=[c.id for c in repo.list_commands()]
    assert ordered[:3]==ids[:3] and ordered[4:]==ids[3:]
    assert_chain(repo,ordered)
    table.selectRow(table.rowCount()-1)
    controller.paste_table_commands('below')
    assert_chain(repo,[c.id for c in repo.list_commands()])
    before_ids=[c.id for c in repo.list_commands()]
    class InternalRowDrop(QDropEvent):
        def source(self):
            return table
    mime=QMimeData();mime.setData(table.ROW_MIME,str(before_ids[-1]).encode('ascii'))
    rect=table.visualItemRect(table.item(1,0))
    drop=InternalRowDrop(QPointF(rect.left()+5,rect.top()+2),Qt.MoveAction,mime,Qt.LeftButton,Qt.NoModifier)
    table.dropEvent(drop)
    assert drop.isAccepted()
    expected=before_ids[:1]+[before_ids[-1]]+before_ids[1:-1]
    assert_chain(repo,expected)
    selected=table.selected_command_ids()
    assert selected==[before_ids[-1]],selected
    window.close(); window.deleteLater();app.sendPostedEvents(None,QEvent.DeferredDelete);app.processEvents()
    print('PASS table: context menu, relative paste, multi-row boundary, existing row drag signal, selected row restoration')


def check_pan(folder,app):
    repo = new_repo(folder/'pan.db')
    ids = repo.append_recording(drafts('A','B'))
    editor=NodeEditorWidget();editor.resize(900,600)
    snapshot=repo.snapshot()
    editor.load_graph(snapshot.nodes,snapshot.edges,INSTRUCTION_SPECS,allow_incomplete=True)
    editor.show();app.processEvents();view=editor.view
    original_positions={key:QPointF(node.pos()) for key,node in editor.scene.nodes_by_id.items()}
    original_edges={(edge.source_node.node_id,edge.target_node.node_id,edge.link_kind) for edge in editor.scene.edges}
    def send(kind,position,button,buttons):
        local=QPointF(position)
        screen=QPointF(view.viewport().mapToGlobal(local.toPoint()))
        event=QMouseEvent(kind,local,screen,button,buttons,Qt.NoModifier)
        app.sendEvent(view.viewport(),event)
        app.processEvents()
    checks=0
    for zoom in (0.35,1.0,1.75):
        view._set_zoom(zoom)
        for target in ('empty','node','edge'):
            if target=='node':
                node=editor.scene.nodes_by_command_id[ids[0]]
                view.centerOn(node)
                start=view.mapFromScene(node.sceneBoundingRect().center())
            elif target=='edge':
                edge=editor.scene.edges[1]
                point=edge.path().pointAtPercent(.5)
                view.centerOn(point)
                start=view.mapFromScene(point)
            else:
                view.centerOn(-3200,-3200)
                start=view.viewport().rect().center()
            app.processEvents()
            if target!='empty':assert view.itemAt(start) is not None,target
            before=view.mapToScene(view.viewport().rect().center())
            end=start+QPoint(110,65)
            send(QEvent.MouseButtonPress,start,Qt.MiddleButton,Qt.MiddleButton)
            assert view._panning,target
            send(QEvent.MouseMove,end,Qt.NoButton,Qt.MiddleButton)
            after=view.mapToScene(view.viewport().rect().center())
            assert abs((before.x()-after.x())-110/zoom)<5/zoom,(target,zoom,before,after)
            assert abs((before.y()-after.y())-65/zoom)<5/zoom,(target,zoom,before,after)
            send(QEvent.MouseButtonRelease,end,Qt.MiddleButton,Qt.NoButton)
            assert not view._panning
            checks+=1
    # Expanding a tiny scene used to invalidate the frozen scrollbar origins.
    editor.scene.setSceneRect(-10,-10,20,20);view.centerOn(0,0)
    start=view.viewport().rect().center();before=view.mapToScene(start)
    send(QEvent.MouseButtonPress,start,Qt.MiddleButton,Qt.MiddleButton)
    send(QEvent.MouseMove,start+QPoint(220,90),Qt.NoButton,Qt.MiddleButton)
    after=view.mapToScene(start)
    assert abs((before.x()-after.x())-220/view._zoom)<6/view._zoom
    app.sendEvent(view,QFocusEvent(QEvent.FocusOut))
    assert not view._panning
    assert all(node.pos()==original_positions[key] for key,node in editor.scene.nodes_by_id.items())
    assert {(edge.source_node.node_id,edge.target_node.node_id,edge.link_kind) for edge in editor.scene.edges}==original_edges
    editor.close();editor.deleteLater();app.sendPostedEvents(None,QEvent.DeferredDelete);app.processEvents()
    print(f'PASS {BINDING}: {checks} middle-button drags on empty/node/edge, zoom, scene expansion, focus loss, nodes/edges unchanged')


def main():
    configure_application();app=QApplication.instance() or QApplication([])
    with tempfile.TemporaryDirectory(prefix='anclicker-table-flow-164-') as folder:
        folder=Path(folder)
        check_repository(folder);check_table(folder,app);check_pan(folder,app)
    app.clipboard().clear()
    app.processEvents()
    print('PASS all table/flow 1.6.4 regressions')
    return 0


if __name__=='__main__':
    raise SystemExit(main())
