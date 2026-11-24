"""Keep dragged geometry and the viewport across connection/settings reloads."""
import os, sys, sqlite3, tempfile
from pathlib import Path
from unittest.mock import patch
sys.path.insert(0, str(Path(__file__).resolve().parents[1]))
from anclicker.platform.qt_compat.QtWidgets import QApplication
from anclicker.platform.qt_compat.QtCore import QPointF, QCoreApplication, QEvent
from anclicker.storage.graph_repository import GraphRepository
from anclicker.domain.instructions import InstructionDraft
from anclicker.ui.instruction_workspace import InstructionWorkspace

app = QApplication([])
with tempfile.TemporaryDirectory() as folder:
    path = str(Path(folder) / 'graph.db')
    with sqlite3.connect(path) as db:
        GraphRepository.initialize_schema(db)
    db.close()
    workspace = InstructionWorkspace(path)
    workspace._show_error = lambda title, error: (_ for _ in ()).throw(AssertionError((title, error)))
    workspace._connection_edit_allowed = lambda: True
    workspace._check_parameter_save_allowed = lambda: None
    repo = workspace.repository
    a = repo.add_command(InstructionDraft('时间等待', {'类型':'时间等待','时长':1,'单位':'秒'}), x=0, y=0, unconnected=True)
    b = repo.add_command(InstructionDraft('时间等待', {'类型':'时间等待','时长':1,'单位':'秒'}), x=400, y=200, unconnected=True)
    workspace.reload_graph()
    workspace.editor.resize(900, 600)
    workspace.editor.show()
    app.processEvents()
    view = workspace.editor.view
    scene = workspace.editor.scene
    view._set_zoom(0.85)
    view._expand_canvas(QPointF(240, 160), view._zoom)
    view.centerOn(240, 160)
    app.processEvents()
    node = scene.nodes_by_command_id[a.id]
    scene.begin_node_drag(node)
    node.setPos(260, -180)
    scene.end_node_drag(node)
    node_id = node.node_id
    target_id = scene.nodes_by_command_id[b.id].node_id
    def capture():
        return (view.transform(), view.mapToScene(view.viewport().rect().center()))
    def verify(before):
        app.processEvents()
        after = capture()
        assert after[0] == before[0], 'zoom changed'
        assert (after[1]-before[1]).manhattanLength() <= 2 / view._zoom, (before[1], after[1])
        item = scene.nodes_by_command_id[a.id]
        assert item.pos() == QPointF(260, -180), item.pos()
        stored = next(n for n in GraphRepository(path).snapshot().nodes if n.node_id == node_id)
        assert (stored.x, stored.y) == (260, -180)
    before = capture()
    workspace._connect_nodes(node_id, target_id)
    verify(before)
    print('PASS dragged coordinates persisted across connection and disk reload; zoom/pan unchanged')
    # Run the real edit/save callback while replacing only the modal UI interaction.
    def save_editor(editor, callback, key):
        draft = editor.get_draft()
        draft.note = 'edited note'
        result = callback(draft)
        editor.deleteLater()
        return result
    before = capture()
    with patch.object(workspace, '_run_parameter_editor', side_effect=save_editor):
        assert workspace.edit_command(a.id)
    verify(before)
    assert repo.get_command(a.id).note == 'edited note'
    print('PASS settings save keeps node coordinates, zoom and pan')
    for _ in range(5):
        workspace.reload_graph(a.id)
    verify(before)
    print('PASS repeated refresh does not accumulate viewport movement')
    workspace.editor.close()
    workspace.editor.deleteLater()
    workspace.palette.deleteLater()
    workspace.deleteLater()
    QCoreApplication.sendPostedEvents(None, QEvent.DeferredDelete)
    app.processEvents()
