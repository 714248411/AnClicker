"""Fresh project transactions and synchronous transparent-shadow cleanup."""
import os
import json
import sys
import tempfile
from pathlib import Path
from unittest.mock import patch
sys.path.insert(0, str(Path(__file__).resolve().parents[1]))
from anclicker.platform.qt_compat.QtWidgets import QApplication, QMessageBox, QDialog
from anclicker.storage.database import DatabaseOperation
from anclicker.storage.data_bundle import apply_import
from anclicker.ui.data_transfer import new_project
from anclicker.ui.project_files import install_new_blank_action
from anclicker.ui.window_edges import install_window_edges
from anclicker.ui.window_shadow import WindowShadow
from tools.check_project_context import Host

app = QApplication.instance() or QApplication([])
with tempfile.TemporaryDirectory() as directory:
    root = Path(directory)
    window = Host(root / 'Data' / '命令集.db')
    (root / 'Data1').mkdir()
    (root / 'Data2').write_text('occupied filename')
    window.db.set_setting_value('全局测试', 'shared')
    window.db.set_setting_value('任务名称', 'old project')
    schedules = json.dumps([{'enabled': True, 'status': 'ready'}])
    window.db.set_setting_value('定时运行任务', schedules)
    install_new_blank_action(window)
    assert [a.objectName() for a in window.menu.actions()][:2] == ['actionNewBlankPage', 'actionNewProject']
    with patch('anclicker.ui.project_changes.is_modified', return_value=True), patch.object(QMessageBox, 'question', return_value=QMessageBox.Cancel):
        assert not new_project(window)
    assert not list(root.glob('.anclicker-import-*'))
    with patch('anclicker.ui.project_changes.is_modified', return_value=True), patch.object(QMessageBox, 'question', return_value=QMessageBox.Yes), patch.object(window, 'save_data', return_value=False):
        assert not new_project(window)
    assert not list(root.glob('.anclicker-import-*'))
    with patch('anclicker.ui.project_changes.is_modified', return_value=False), patch.object(window, 'close', return_value=False):
        assert not new_project(window)
    assert not getattr(app, '_whole_data_import', None)
    assert not list(root.glob('.anclicker-import-*'))
    with patch('anclicker.ui.project_changes.is_modified', return_value=False), patch.object(window, 'close', return_value=True), patch.object(app, 'quit') as quit_app:
        assert new_project(window)
        quit_app.assert_called_once()
    stage, destination, adapt, fresh, own_project = app._whole_data_import
    assert Path(destination) == root / 'Data3'
    apply_import(stage, destination, adapt=adapt, new_partition=fresh, remember=True, disable_schedules=not own_project)
    db = DatabaseOperation(str(Path(destination) / '命令集.db'))
    assert db.get_setting_value('全局测试') == 'shared'
    assert db.get_setting_value('定时运行任务') == schedules
    assert db.get_setting_value('任务名称') != 'old project'
    assert db.get_setting_value('本机项目默认保存目录') == destination
    assert Path(db.get_setting_value('当前文件路径')) == Path(destination) / '空白页1.xlsx'
    assert (Path(destination) / '空白页1.xlsx').is_file()
    assert not db.get_graph_repository().list_commands()
    assert window.db.get_setting_value('任务名称') == 'old project'
    app._whole_data_import = None
    window.close()

install_window_edges()
dialog = QDialog()
dialog.show()
shadow = dialog._outer_shadow = WindowShadow(dialog)
shadow.sync(False)
assert shadow.isVisible()
dialog.hide()
# No processEvents: an import can block immediately after this point.
assert not shadow.isVisible(), 'hidden dialog left a transparent shadow on screen'
dialog.deleteLater()
print('PASS new project menu, cancellation, refused close, occupied names, defaults/global settings, active page and immediate shadow cleanup')
