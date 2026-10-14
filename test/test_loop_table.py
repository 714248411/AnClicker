from unittest.mock import patch
import pytest
from openpyxl import Workbook
from qt_compat.QtCore import Qt, QTimer
from qt_compat.QtGui import QContextMenuEvent
from qt_compat.QtWidgets import QApplication
from flow_loop_table import aligned_loop_order, loop_groups
from test.test_control_priority import Graph, return_loop
from test.test_hidden_stop import host
from graph_repository import GraphRepository
from 数据库操作 import DatabaseOperation


def test_order_groups_body_preserves_edges_positions_and_local_jump(tmp_path):
    graph = Graph(tmp_path/'g.db')
    a, b, loop = return_loop(graph)
    compare = graph.add('compare', '变量比较', 变量='n', 是跳转方式='当前项目行', 是目标行=2,
                        否跳转方式='其他项目行', 否目标行=2, 否项目路径='other.xlsx')
    before = graph.repo.snapshot()
    by_name = {name: ident for ident, name in graph.names.items()}
    assert graph.repo.align_loop_orders()
    after = graph.repo.snapshot()
    assert [c.id for c in after.commands] == [by_name[n] for n in ('L', 'A', 'B', 'compare')]
    assert before.edges == after.edges
    assert {(n.node_id, n.x, n.y) for n in before.nodes} == {(n.node_id, n.x, n.y) for n in after.nodes}
    params = after.commands[-1].parameters
    assert params['是目标行'] == 3 and params['否目标行'] == 2
    assert not graph.repo.align_loop_orders()
    workbook = Workbook()
    graph.repo.export_to_workbook(workbook, graph.db)
    db = DatabaseOperation(str(tmp_path/'reopened.db'))
    restored = GraphRepository(db.db_path)
    restored.import_from_workbook(workbook)
    assert restored.list_commands() == graph.repo.list_commands()
    assert restored.snapshot().edges == after.edges


def make_host_loop(host):
    repo = host.workspace.repository
    repo.clear()
    graph = Graph.__new__(Graph)
    graph.repo, graph.names = repo, {}
    return_loop(graph)
    host.workspace.reload_graph()
    host.view_workspace.refresh_all()
    host.tabWidget.setCurrentIndex(1)
    QApplication.processEvents()
    return graph, host.view_workspace.command_table


def test_right_click_collapse_expand_keeps_loop_and_continuation_visible(host):
    graph, table = make_host_loop(host)
    names = [graph.names[table.item(row, 0).data(Qt.UserRole)] for row in range(table.rowCount())]
    assert names == ['L', 'A', 'B']
    header = table.item(0, 0).data(Qt.UserRole)
    pos = table.visualRect(table.model().index(0, 2)).center()
    labels = []
    def choose():
        menu = QApplication.activePopupWidget()
        labels.extend(a.text() for a in menu.actions())
        next(a for a in menu.actions() if a.text() == '收起循环内容').trigger()
        menu.close()
    QTimer.singleShot(30, choose)
    table.contextMenuEvent(QContextMenuEvent(QContextMenuEvent.Mouse, pos, table.mapToGlobal(pos)))
    assert '展开循环内容' in labels
    assert [table.isRowHidden(i) for i in range(3)] == [False, True, False]
    host.view_workspace.refresh_all()
    assert table.isRowHidden(1) and table.item(0, 2).text().startswith('▸')
    assert [n for n in graph.run() if n != 'L'] == ['A']*3+['B']
    table.set_loop_collapsed(header, False)
    assert not any(table.isRowHidden(i) for i in range(3))


def test_nested_fold_survives_outer_expansion_and_removed_links(host):
    graph, table = make_host_loop(host)
    outer = graph.add('outer', '循环', 次数=2)
    nodes = {graph.names[n.command_id]: n.node_id for n in graph.repo.snapshot().nodes if n.command_id}
    graph.repo.delete_connection('start', nodes['A'])
    graph.link('start', outer)
    graph.link(outer, nodes['L'], 3)
    graph.link(nodes['B'], outer)
    host.workspace.reload_graph()
    host.view_workspace.refresh_all()
    ids = {name: ident for ident, name in graph.names.items()}
    table.set_loop_collapsed(ids['L'], True)
    table.set_loop_collapsed(ids['outer'], True)
    assert sum(not table.isRowHidden(i) for i in range(4)) == 1
    table.set_loop_collapsed(ids['outer'], False)
    assert sum(table.isRowHidden(i) for i in range(4)) == 1
    graph.repo.delete_connection(nodes['L'], nodes['A'])
    host.workspace.reload_graph()
    host.view_workspace.refresh_all()
    assert ids['L'] not in table.collapsed_loops


def test_running_folded_body_highlights_header_without_changing_selection(host):
    graph, table = make_host_loop(host)
    ids = {name: ident for ident, name in graph.names.items()}
    table.setCurrentCell(2, 3)
    selection = table.selected_command_ids()
    table.set_loop_collapsed(ids['L'], True)
    host.view_workspace.highlight_running_command(ids['A'])
    assert table.runtime_row == 0 and table.isRowHidden(1)
    assert table.selected_command_ids() == selection
