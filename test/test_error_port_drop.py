from unittest.mock import patch
import pytest
from qt_compat.QtCore import QPointF, Qt, QTimer, QEvent
from qt_compat.QtGui import QMouseEvent
from qt_compat.QtWidgets import QApplication, QMessageBox
from qt_compat.QtTest import QTest
from graph_repository import GraphRepository, GraphValidationError, START_NODE_ID
from instructions.models import InstructionDraft
from 数据库操作 import DatabaseOperation
from test.test_hidden_stop import host
from test.test_cad_canvas import canvas


@pytest.fixture
def repository(tmp_path):
    database = DatabaseOperation(str(tmp_path / 'error-drop.db'))
    repo = GraphRepository(str(tmp_path / 'error-drop.db'))
    command = repo.add_command(InstructionDraft('时间等待', {'时长': 0}))
    source = next(node.node_id for node in repo.snapshot().nodes if node.command_id == command.id)
    return repo, source


def test_handler_and_error_link_created_at_drop_position_without_changing_main_flow(repository):
    repo, source = repository
    before = repo.snapshot()
    command = repo.add_error_handler(source, 713.5, -230.25)
    after = repo.snapshot()
    node = next(node for node in after.nodes if node.command_id == command.id)
    assert command.type_id == '报错跳转'
    assert command.parameters == {'跳转方式': '连线节点', '目标行': 1, '项目路径': ''}
    assert (node.x, node.y) == (713.5, -230.25)
    assert after.commands[:-1] == before.commands
    assert set(after.edges) - set(before.edges) == {__import__('graph_repository').EdgeRecord(source, node.node_id, 5)}
    repo.connect_nodes(node.node_id, 'end')
    assert any(edge.source == node.node_id and edge.kind == 6 for edge in repo.snapshot().edges)


def test_repeated_drop_does_not_leave_an_orphan_handler(repository):
    repo, source = repository
    repo.add_error_handler(source, 400, 300)
    before = repo.snapshot()
    with pytest.raises(GraphValidationError, match='已连接'):
        repo.add_error_handler(source, 800, 300)
    assert repo.snapshot() == before


def test_failed_error_link_validation_rolls_back_module_and_edge(repository):
    repo, source = repository
    before = repo.snapshot()
    with patch.object(repo, '_validate_draft_connection', side_effect=GraphValidationError('拒绝连接')):
        with pytest.raises(GraphValidationError, match='拒绝连接'):
            repo.add_error_handler(source, 400, 300)
    assert repo.snapshot() == before


@pytest.mark.parametrize('source', ['missing', START_NODE_ID, 'end'])
def test_missing_or_terminal_source_cannot_create_handler(repository, source):
    repo, _ = repository
    before = repo.snapshot()
    with pytest.raises(GraphValidationError):
        repo.add_error_handler(source, 100, 200)
    assert repo.snapshot() == before


def load_scene(scene):
    scene.load_graph([{'id': 1, 'type_id': '时间等待', 'x': 0, 'y': 0},
                      {'id': 2, 'type_id': '报错跳转', 'x': 400, 'y': 0}], [], {})
    return scene.nodes_by_command_id[1], scene.nodes_by_command_id[2]


def test_only_error_port_on_empty_canvas_requests_new_module(canvas):
    scene, _ = canvas
    source, handler = load_scene(scene)
    requested, connected = [], []
    scene.errorNodeRequested.connect(lambda *args: requested.append(args))
    scene.branchConnectionRequested.connect(lambda *args: connected.append(args))
    blank = QPointF(1000, 600)
    for port in (source.output_port, source.input_port, handler.output_port):
        scene.begin_port_connection(port)
        scene.end_port_connection(blank)
    assert not requested
    scene.begin_port_connection(source.error_port)
    assert scene._connection_preview.pen().color().name() == '#d99653'
    scene.update_port_connection(blank)
    scene.end_port_connection(blank)
    assert requested == [(source.node_id, 1000, 600)]
    assert scene._connection_port is None and scene._connection_preview is None
    scene.begin_port_connection(source.error_port)
    scene.end_port_connection(handler.sceneBoundingRect().center())
    assert connected == [(source.node_id, handler.node_id, 5)]
    assert len(requested) == 1
    scene.addRect(900, 500, 200, 200)
    scene.begin_port_connection(source.error_port)
    scene.end_port_connection(blank)
    assert len(requested) == 1


@pytest.fixture
def workspace(host):
    workspace = host.workspace
    workspace.reload_graph()
    host.tabWidget.setCurrentIndex(2)
    QApplication.processEvents()
    return workspace


@pytest.mark.parametrize('choice', ['enter', 'button', 'cancel'])
def test_real_drag_prompts_and_default_enter_or_button_adds_connected_handler(workspace, choice):
    repo, scene, view = workspace.repository, workspace.editor.scene, workspace.editor.view
    source = next(node for node in scene.nodes_by_id.values() if node.command_id is not None)
    view._set_zoom(1)
    view.centerOn(source.scenePos() + QPointF(200, 100))
    QApplication.processEvents()
    blank = QPointF(source.scenePos() + QPointF(400, 230))
    assert not scene.items(blank)
    original = repo.snapshot()
    transform = view.transform()
    center = view.mapToScene(view.viewport().rect().center())
    dialogs = []
    def answer():
        box = QApplication.activeModalWidget()
        if not isinstance(box, QMessageBox):
            dialogs.append('missing dialog')
            return
        dialogs.append((box.windowTitle(), box.defaultButton().text()))
        if choice == 'button':
            QTest.mouseClick(box.defaultButton(), Qt.LeftButton)
        else:
            QTest.keyClick(box, Qt.Key_Escape if choice == 'cancel' else Qt.Key_Return)
    # Start at the real port; reload is queued until mouseReleaseEvent completes.
    QTest.mousePress(view.viewport(), Qt.LeftButton, pos=view.mapFromScene(source.error_port.scenePos()))
    assert scene._connection_port is source.error_port
    QApplication.sendEvent(view.viewport(), QMouseEvent(
        QEvent.MouseMove, QPointF(view.mapFromScene(blank)), Qt.NoButton, Qt.LeftButton, Qt.NoModifier))
    timer = QTimer()
    timer.setSingleShot(True)
    timer.timeout.connect(answer)
    timer.start(50)
    with patch.object(workspace, '_show_error', side_effect=AssertionError('Unexpected creation error')):
        QTest.mouseRelease(view.viewport(), Qt.LeftButton, pos=view.mapFromScene(blank))
        QApplication.processEvents()
        QTest.qWait(100)
    timer.stop()
    assert dialogs == [('添加报错模块', '添加报错模块')]
    after = repo.snapshot()
    if choice == 'cancel':
        assert after == original
    else:
        assert len(after.commands) == len(original.commands) + 1
        handler = next(node for node in after.nodes if node.type_id == '报错跳转')
        assert abs(handler.x - blank.x()) <= 1 and abs(handler.y - blank.y()) <= 1
        assert any(edge.source == source.node_id and edge.target == handler.node_id and edge.kind == 5 for edge in after.edges)
        assert view.transform() == transform
        assert (view.mapToScene(view.viewport().rect().center()) - center).manhattanLength() <= 2
        assert scene.nodes_by_id[handler.node_id].isSelected()
        assert not view._arrow_timer.isActive()


def test_existing_binding_or_running_task_does_not_offer_new_module(workspace):
    repo = workspace.repository
    source = next(node.node_id for node in repo.snapshot().nodes if node.command_id is not None)
    repo.add_error_handler(source, 500, 200)
    before = repo.snapshot()
    with patch('instruction_workspace.QMessageBox') as dialog:
        workspace._add_error_node(source, 800, 200)
        dialog.assert_not_called()
    with patch.object(workspace.parent_window.command_thread, 'isRunning', return_value=True), patch('instruction_workspace.QMessageBox') as dialog:
        workspace._add_error_node(source, 800, 200)
        dialog.assert_not_called()
    assert repo.snapshot() == before
