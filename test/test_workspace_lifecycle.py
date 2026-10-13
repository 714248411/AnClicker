"""A discarded workspace must release its Qt graph without cyclic GC crashes."""
import gc
import weakref
from qt_compat.QtWidgets import QApplication
from instruction_workspace import InstructionWorkspace
from instructions.models import InstructionDraft
from 数据库操作 import DatabaseOperation


def test_workspaces_release_immediately_and_stale_callbacks_are_safe(tmp_path):
    app = QApplication.instance() or QApplication([])
    for i in range(20):
        db = DatabaseOperation(str(tmp_path / f'graph-{i}.db'))
        workspace = InstructionWorkspace(db.db_path)
        workspace.repository.add_command(InstructionDraft('条件判断', {'条件': 'True'}), unconnected=True)
        workspace.reload_graph()
        reference = weakref.ref(workspace)
        callbacks = (workspace.editor.view.template_names_provider,
                     workspace.editor.view.can_cut_connections,
                     workspace.editor.view.connection_undo_count,
                     workspace.editor.view.connection_redo_count)
        assert callbacks[2]() == 0
        workspace.editor.close()
        workspace.palette.close()
        del workspace
        # Collection must happen by Qt ownership/refcounts, not by a cyclic GC
        # pass deleting graphics parents and children in an arbitrary order.
        assert reference() is None
        assert [callback() for callback in callbacks] == [(), False, 0, 0]
        gc.collect()
        app.processEvents()
