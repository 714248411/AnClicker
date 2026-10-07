import pytest
from PySide6.QtCore import Qt, QTimer
from PySide6.QtGui import QContextMenuEvent
from PySide6.QtTest import QTest
from PySide6.QtWidgets import QApplication
from test.test_hidden_stop import host
from instructions.models import InstructionDraft
from node_editor.items import EdgeItem


@pytest.fixture
def flow(host):
    repo = host.workspace.repository
    repo.clear()
    commands = [repo.add_command(InstructionDraft('时间等待', {'时长': 0}), unconnected=True) for _ in range(3)]
    host.workspace.reload_graph()
    nodes = {n.command_id: n.node_id for n in repo.snapshot().nodes if n.command_id}
    return host, [nodes[c.id] for c in commands]


def test_default_option_position_persistence_and_compact_mode(host):
    check = host.run_unconnected_checkbox
    assert check.isChecked()
    assert check.parentWidget().layout().indexOf(check) < check.parentWidget().layout().indexOf(host.checkBox_2)
    check.setChecked(False)
    assert host.db.get_setting_value('运行未连接模块') == 'False'
    host.view_workspace.refresh_all()
    assert not check.isChecked()
    host.view_workspace.compact.set_active(True)
    assert check.isVisible()
    host.view_workspace.compact.set_active(False)
    assert not check.isChecked()


def test_single_edge_delete_undo_preserves_other_edges_and_commands(flow):
    host, (a, b, c) = flow
    w = host.workspace
    w._connect_nodes(a, b)
    w._connect_nodes(b, c)
    before = w.repository.snapshot()
    w._delete_edge(a, b)
    assert [(e.source, e.target) for e in w.repository.snapshot().edges] == [(b, c)]
    assert w.repository.list_commands() == list(before.commands)
    w.undo_connections()
    assert w.repository.snapshot().edges == before.edges
    assert len(w._connection_history) == 2
    w.undo_connections()
    assert [(e.source, e.target) for e in w.repository.snapshot().edges] == [(a, b)]


def test_history_limit_twenty_and_noop_does_not_use_step(flow):
    host, (a, b, _) = flow
    w = host.workspace
    for _ in range(12):
        w._connect_nodes(a, b)
        w._delete_edge(a, b)
    assert len(w._connection_history) == 20
    w._delete_edge(a, b)
    assert len(w._connection_history) == 20
    for _ in range(20):
        w.undo_connections()
    assert not w._connection_history
    before = w.repository.snapshot()
    w.undo_connections()
    assert w.repository.snapshot().edges == before.edges


def test_branch_roles_survive_group_delete_and_undo(flow):
    host, (a, b, c) = flow
    w = host.workspace
    repo = w.repository
    cmd = repo.add_command(InstructionDraft('条件判断', {'条件': 'True'}), unconnected=True)
    cond = next(n.node_id for n in repo.snapshot().nodes if n.command_id == cmd.id)
    w.reload_graph()
    w._connect_nodes(cond, a, 2)
    w._connect_nodes(cond, b, 1)
    before = repo.snapshot()
    w._delete_connections(cond, 'outgoing')
    assert not repo.snapshot().edges
    w.undo_connections()
    assert repo.snapshot().edges == before.edges


def test_node_changes_invalidate_history(flow):
    host, (a, b, c) = flow
    w = host.workspace
    w._connect_nodes(a, b)
    assert w._connection_history
    w.repository.add_command(InstructionDraft('时间等待', {'时长': 0}), unconnected=True)
    w.reload_graph()
    assert not w._connection_history


def test_running_blocks_connection_mutations(flow, monkeypatch):
    host, (a, b, c) = flow
    w = host.workspace
    w._connect_nodes(a, b)
    before = w.repository.snapshot().edges
    monkeypatch.setattr(host.command_thread, 'isRunning', lambda: True)
    w._delete_edge(a, b)
    w._delete_connections(a, 'all')
    w._connect_nodes(b, c)
    w.undo_connections()
    assert w.repository.snapshot().edges == before
    monkeypatch.undo()


def test_right_click_edge_deletes_only_that_edge(flow):
    host, (a, b, _) = flow
    w = host.workspace
    w.repository.save_node_position(a, 0, 0)
    w.repository.save_node_position(b, 800, 0)
    w._connect_nodes(a, b)
    host.tabWidget.setCurrentIndex(2)
    view = w.editor.view
    view.fit_graph()
    QApplication.processEvents()
    edge = w.editor.scene.edges[0]
    pos = view.mapFromScene(edge.path().pointAtPercent(.5))
    assert isinstance(view.itemAt(pos), EdgeItem)
    observed = []
    def choose():
        menu = QApplication.activePopupWidget()
        observed.extend(a.text() for a in menu.actions())
        action = next(a for a in menu.actions() if a.text() == '删除此连线')
        menu.setActiveAction(action)
        QTest.keyClick(menu, Qt.Key.Key_Return)
    QTimer.singleShot(20, choose)
    view.contextMenuEvent(QContextMenuEvent(QContextMenuEvent.Reason.Mouse, pos, view.mapToGlobal(pos)))
    assert not w.repository.snapshot().edges
    assert any('20 步' in text for text in observed)
