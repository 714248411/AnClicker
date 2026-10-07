from test.test_connection_history import host, flow
from PySide6.QtCore import QTimer, Qt
from PySide6.QtGui import QContextMenuEvent
from PySide6.QtWidgets import QApplication
from PySide6.QtTest import QTest
from instructions.models import InstructionDraft
import pytest

def test_control_option_default_position_and_persistence(host):
    check=host.run_unconnected_checkbox
    assert check.isChecked()
    assert check.parentWidget().layout().indexOf(check)<check.parentWidget().layout().indexOf(host.checkBox_2)
    check.setChecked(False)
    assert host.db.get_setting_value('运行未连接模块')=='False'
    host.view_workspace.refresh_all()
    assert not check.isChecked()
    host.view_workspace.compact.set_active(True)
    assert check.isVisible()
    host.view_workspace.compact.set_active(False)
    assert not check.isChecked()

def context(view, pos, choose=None):
    texts=[]
    def act():
        menu=QApplication.activePopupWidget()
        texts.extend(a.text() for a in menu.actions())
        action=next((a for a in menu.actions() if a.text()==choose),None)
        if action is None:
            menu.close()
        else:
            menu.setActiveAction(action)
            QTest.keyClick(menu,Qt.Key.Key_Return)
    QTimer.singleShot(20,act)
    view.contextMenuEvent(QContextMenuEvent(QContextMenuEvent.Reason.Mouse,pos,view.mapToGlobal(pos)))
    return texts

def layout(host, ids):
    w=host.workspace
    for index,node in enumerate(ids):
        w.repository.save_node_position(node,index*800,0)
    w.reload_graph()
    host.tabWidget.setCurrentIndex(2)
    w.editor.view.fit_graph()
    QApplication.processEvents()
    return w,w.editor.view

@pytest.mark.parametrize('label,remaining',[
    ('删除前流程连接线',1),('删除后流程连接线',0),('删除流程连接线',None)])
def test_multiselect_node_keeps_original_menu_and_targets_clicked_node(flow,label,remaining):
    host,ids=flow
    a,b,c=ids
    w,view=layout(host,ids)
    w._connect_nodes(a,b); w._connect_nodes(b,c)
    before=w.repository.snapshot()
    for node in ids:w.editor.scene.nodes_by_id[node].setSelected(True)
    for edge in w.editor.scene.edges:edge.setSelected(True)
    node=w.editor.scene.nodes_by_id[b]
    pos=view.mapFromScene(node.sceneBoundingRect().center())
    texts=context(view,pos,label)
    for expected in ('配置','备注','复制','删除','删除流程连接线','删除前流程连接线','删除后流程连接线'):
        assert expected in texts
    assert any('撤销连线' in t for t in texts)
    assert any('回退连线' in t for t in texts)
    assert tuple(w.repository.snapshot().edges)==(() if remaining is None else (before.edges[remaining],))
    assert w.repository.snapshot().commands==before.commands
    w.undo_connections()
    assert w.repository.snapshot().edges==before.edges
    w.redo_connections()
    assert len(w.repository.snapshot().edges)==(0 if remaining is None else 1)

def test_selected_edges_batch_delete_is_one_step_and_does_not_delete_nodes(flow):
    host,ids=flow
    a,b,c=ids
    w,view=layout(host,ids)
    w._connect_nodes(a,b); w._connect_nodes(b,c)
    before=w.repository.snapshot()
    history=len(w._connection_history)
    for edge in w.editor.scene.edges:edge.setSelected(True)
    edge=w.editor.scene.edges[0]
    pos=view.mapFromScene(edge.path().pointAtPercent(.5))
    texts=context(view,pos,'删除选中连线（2 根）')
    assert '配置' not in texts
    assert not w.repository.snapshot().edges
    assert w.repository.snapshot().commands==before.commands
    assert len(w._connection_history)==history+1
    w.undo_connections(); assert w.repository.snapshot().edges==before.edges
    w.redo_connections(); assert not w.repository.snapshot().edges

def test_redo_invalidated_by_new_edit_and_node_change(flow,monkeypatch):
    host,(a,b,c)=flow
    w=host.workspace
    w._connect_nodes(a,b); w.undo_connections()
    assert len(w._connection_redo)==1
    monkeypatch.setattr(host.command_thread,'isRunning',lambda:True)
    w.redo_connections(); assert not w.repository.snapshot().edges
    monkeypatch.undo()
    w._connect_nodes(b,c)
    assert not w._connection_redo
    w.undo_connections()
    w.repository.add_command(InstructionDraft('时间等待',{'时长':0}),unconnected=True)
    w.reload_graph()
    assert not w._connection_redo and not w._connection_history

def test_twenty_undo_redo_round_trip(flow):
    host,(a,b,c)=flow
    w=host.workspace
    for _ in range(12):
        w._connect_nodes(a,b); w._delete_edge(a,b)
    expected=w.repository.snapshot()
    for _ in range(20):w.undo_connections()
    assert len(w._connection_redo)==20
    for _ in range(20):w.redo_connections()
    assert w.repository.snapshot().edges==expected.edges
    assert w.repository.snapshot().commands==expected.commands
    assert len(w._connection_history)==20 and not w._connection_redo

def test_rubberband_edges_menu_in_selection_area(flow):
    from PySide6.QtGui import QPainterPath
    from node_editor.items import EdgeItem
    host,(a,b,c)=flow
    w,view=layout(host,(a,b,c))
    w.repository.save_node_position(c,800,500)
    w._connect_nodes(a,b);w._connect_nodes(a,c)
    area=QPainterPath()
    area.addRect(w.editor.scene.itemsBoundingRect().adjusted(-20,-20,20,20))
    w.editor.scene.setSelectionArea(area)
    assert all(e.isSelected() for e in w.editor.scene.edges)
    bounds=w.editor.scene.edges[0].sceneBoundingRect()
    for edge in w.editor.scene.edges[1:]:bounds=bounds.united(edge.sceneBoundingRect())
    pos=None
    for x in range(int(bounds.left())+20,int(bounds.right()),20):
        for y in range(int(bounds.top())+20,int(bounds.bottom()),20):
            from PySide6.QtCore import QPointF
            point=view.mapFromScene(QPointF(x,y))
            if view.viewport().rect().contains(point) and view.itemAt(point) is None:
                pos=point;break
        if pos is not None:break
    assert pos is not None
    texts=context(view,pos,'删除选中连线（2 根）')
    assert not w.repository.snapshot().edges
    assert len(w.repository.list_commands())==3

def test_branch_roles_redo_and_failed_restore_preserve_history(flow,monkeypatch):
    host,(a,b,c)=flow
    w=host.workspace
    command=w.repository.add_command(InstructionDraft('条件判断',{'条件':'True'}),unconnected=True)
    cond=next(n.node_id for n in w.repository.snapshot().nodes if n.command_id==command.id)
    w.reload_graph();w._connect_nodes(cond,a,2);w._connect_nodes(cond,b,1)
    before=w.repository.snapshot()
    w._delete_edges([(cond,a),(cond,b)]);w.undo_connections()
    assert w.repository.snapshot().edges==before.edges
    with monkeypatch.context() as m:
        m.setattr(w.repository,'restore_connections',lambda *args:(_ for _ in ()).throw(RuntimeError('test failure')))
        m.setattr(w,'_show_error',lambda *args:None)
        w.redo_connections()
        assert len(w._connection_redo)==1
        assert w.repository.snapshot().edges==before.edges
    w.redo_connections();assert not w.repository.snapshot().edges
    w.undo_connections();assert w.repository.snapshot().edges==before.edges

def test_identical_project_import_clears_both_histories(flow):
    from openpyxl import Workbook
    host,(a,b,c)=flow
    w=host.workspace
    w._connect_nodes(a,b);w._connect_nodes(b,c);w.undo_connections()
    assert w._connection_history and w._connection_redo
    workbook=Workbook()
    try:
        w.repository.export_to_workbook(workbook,host.db)
        w.repository.import_from_workbook(workbook)
        w.clear_connection_history()
        w.reload_graph()
        assert not w._connection_history and not w._connection_redo
    finally:
        workbook.close()
