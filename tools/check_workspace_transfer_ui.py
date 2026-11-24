"""Transfer menu selection and cancellation never mutate a project or close the app."""
import os
from pathlib import Path
import sys
import tempfile
from unittest.mock import patch

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))
from anclicker.platform.qt_compat.QtWidgets import QApplication, QMessageBox
from anclicker.storage.database import DatabaseOperation
from anclicker.storage.workspace_bundle import export_workspace
from anclicker.ui.data_transfer import export_selected_project, import_workspace
from tools.check_project_context import Host

app = QApplication.instance() or QApplication([])
with tempfile.TemporaryDirectory() as directory:
    root = Path(directory)
    window = Host(root / 'Data' / '命令集.db')
    data2 = root / 'Data2'
    data2.mkdir()
    DatabaseOperation(str(data2 / '命令集.db'))
    window.db.set_setting_value('本机项目默认保存目录', str(data2))
    labels = [f'{root.name} — {root}' for root in (root / 'Data', data2)]
    with patch('anclicker.ui.data_transfer.QInputDialog.getItem', return_value=(labels[0], True)) as dropdown, patch('anclicker.ui.data_transfer._export') as export:
        export_selected_project(window)
        assert dropdown.call_args.args[3:6] == (labels, 1, False)
        export.assert_called_once_with(window, root / 'Data')
    assert window.db.get_setting_value('本机项目默认保存目录') == str(data2)
    with patch('anclicker.ui.data_transfer.QInputDialog.getItem', return_value=('', False)), patch('anclicker.ui.data_transfer._export') as export:
        export_selected_project(window)
        export.assert_not_called()
    archive = export_workspace(window.db, root / 'all.zip')
    before = Path(window.db.db_path).read_bytes()
    with patch('anclicker.ui.data_transfer.QFileDialog.getOpenFileName', return_value=(str(archive), '')), patch('anclicker.ui.data_transfer.QMessageBox.question', return_value=QMessageBox.No), patch.object(window, 'close') as close:
        import_workspace(window)
        close.assert_not_called()
    assert not list(root.glob('.anclicker-import-*'))
    assert Path(window.db.db_path).read_bytes() == before
    assert not getattr(app, '_whole_workspace_import', None)
    # A refused close must clear the handoff and discard staging as well.
    with patch('anclicker.ui.data_transfer.QFileDialog.getOpenFileName', return_value=(str(archive), '')), patch('anclicker.ui.data_transfer.QMessageBox.question', return_value=QMessageBox.Yes), patch.object(window, 'close', return_value=False):
        import_workspace(window)
    assert not getattr(app, '_whole_workspace_import', None)
    assert not list(root.glob('.anclicker-import-*'))
    assert Path(window.db.db_path).read_bytes() == before
    window.close()
print('PASS export dropdown defaults to current project, alternate selection, cancel, import confirmation cancellation and refused-close cleanup')
