import pytest
from qt_compat.QtCore import QEvent, QPointF, Qt
from qt_compat.QtGui import QMouseEvent, QKeyEvent
from qt_compat.QtWidgets import QApplication
from test.test_connection_history import host, flow


def send(view, kind, point, button, buttons):
    event = QMouseEvent(kind, QPointF(point), QPointF(view.viewport().mapToGlobal(point.toPoint())), button, buttons, Qt.ControlModifier)
    QApplication.sendEvent(view.viewport(), event)


@pytest.mark.parametrize('cancel', [False, True])
def test_copy_group_moves_only_its_members_and_saves(flow, cancel, monkeypatch):
    window, ids = flow
    workspace = window.workspace
    ids = [workspace.editor.scene.nodes_by_id[key].command_id for key in ids]
    def fail(title, error):
        raise error
    monkeypatch.setattr(workspace, "_show_error", fail)
    copied = workspace.copy_commands(ids[:2])
    other = workspace.copy_commands(ids[2:])
    view = workspace.editor.view
    scene = workspace.editor.scene
    view.resize(900, 600)
    view.show()
    node = scene.nodes_by_command_id[copied[0]]
    view.centerOn(node.sceneBoundingRect().center())
    QApplication.processEvents()
    before = {key: QPointF(n.pos()) for key, n in scene.nodes_by_command_id.items()}
    point = QPointF(view.mapFromScene(node.sceneBoundingRect().center()))
    saved = []
    original_save = workspace.repository.save_node_positions
    def batch_save(positions):
        saved.append(dict(positions))
        original_save(positions)
    monkeypatch.setattr(workspace.repository, "save_node_positions", batch_save)
    end = point + QPointF(45, 30)
    send(view, QEvent.MouseButtonPress, point, Qt.LeftButton, Qt.LeftButton)
    assert view._group_drag is not None
    send(view, QEvent.MouseMove, end, Qt.NoButton, Qt.LeftButton)
    delta = scene.nodes_by_command_id[copied[0]].pos() - before[copied[0]]
    assert not delta.isNull()
    for key, start in before.items():
        assert scene.nodes_by_command_id[key].pos() == start + (delta if key in copied else QPointF())
    if cancel:
        view.keyPressEvent(QKeyEvent(QEvent.KeyPress, Qt.Key_Escape, Qt.NoModifier))
    send(view, QEvent.MouseButtonRelease, end, Qt.LeftButton, Qt.NoButton)
    assert view._group_drag is None
    assert len(saved) == (0 if cancel else 1)
    if not cancel:
        assert len(saved[0]) == len(copied)
    workspace.reload_graph()
    for key, start in before.items():
        assert scene.nodes_by_command_id[key].pos() == start + (delta if key in copied and not cancel else QPointF())
    # Group membership survives an ordinary graph refresh.
    copied_nodes = {scene.nodes_by_command_id[key].node_id for key in copied}
    assert any(copied_nodes == group for group in view._copied_groups)
