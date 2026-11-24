"""Project roots and page parameters persist; software preferences stay global."""
from pathlib import Path
import json
import sys
import tempfile
from types import SimpleNamespace
from unittest.mock import patch
import openpyxl
if __package__ in (None, ''):
    sys.path.insert(0, str(Path(__file__).resolve().parents[1]))
from anclicker.platform.qt_compat.QtWidgets import QApplication, QRadioButton, QSpinBox, QCheckBox, QMessageBox
from anclicker.storage.database import DatabaseOperation
from anclicker.domain.instructions import InstructionDraft
from anclicker.ui.project_files import PROJECT_DIRECTORY, project_directory, new_blank_page
from anclicker.ui.project_changes import mark_clean, is_modified
from anclicker.ui.project_run_controls import ProjectRunControls, CACHE_KEY
from tools.check_xlsm_drop import DropHost


class Host(DropHost):
    def __init__(self, path):
        super().__init__(path)
        self.radioButton = QRadioButton(self)
        self.radioButton_2 = QRadioButton(self)
        self.spinBox = QSpinBox(self)
        self.spinBox.setRange(1, 99999)
        self.run_unconnected_checkbox = QCheckBox(self)
        self.checkBox_2 = QCheckBox(self)
        self.view_workspace.recording_page = SimpleNamespace(busy=False, drafts=[], written=True, clear=lambda: None)
        self.project_run_controls = ProjectRunControls(self)


def main():
    app = QApplication.instance() or QApplication([])
    with tempfile.TemporaryDirectory() as directory:
        root = Path(directory)
        data2 = root / 'Data2'
        nested = data2 / '子页面'
        nested.mkdir(parents=True)
        window = Host(root / 'Data' / 'task.db')
        db, repo = window.db, window.workspace.repository
        global_values = {'界面主题': 'dark', '快捷键-开始运行': 'f9', '小窗口大小模式': 'last'}
        db.set_setting_values(dict(global_values, **{PROJECT_DIRECTORY: str(data2)}))
        db.save_window_size(900, 600, 'main', position=(40, 50))
        geometry = db.get_window_state('main')
        repo.append_recording([InstructionDraft('时间等待', {'类型': '时间等待', '时长': 0, '单位': '秒'})])
        page = nested / '任务.xlsx'
        book = openpyxl.Workbook()
        repo.export_to_workbook(book, db)
        # Old workbooks exported global preferences; opening them must no longer apply these.
        for name, value in {'界面主题': 'light', '快捷键-开始运行': 'f2', '小窗口大小模式': 'default'}.items():
            book['设置'].append(['设置', name, value, None, None])
        book['设置'].append(['窗口大小', 'main-1920*1080', '[300,200]', None, None])
        book.save(page)
        book.close()
        window.data_import(str(page))
        assert project_directory(db) == str(data2)
        assert db.get_setting_values(list(global_values)) == global_values
        assert db.get_window_state('main') == geometry

        window.radioButton_2.setChecked(True)
        window.spinBox.setValue(7)
        window.radioButton.setChecked(True)
        window.checkBox_2.setChecked(True)
        window.run_unconnected_checkbox.setChecked(False)
        db.set_setting_values({'任务名称': '项目二', '绑定窗口标题': '目标窗口'})
        resources = data2 / '项目资源'
        resources.mkdir()
        db.writes_to_resource_folder_path(str(resources))
        controls = window.project_run_controls.values()
        saved_resources = db.extract_resource_folder_path()
        # A historical empty page carries old parameters and must remain untouched.
        stale = data2 / '空白页1.xlsx'
        old = openpyxl.Workbook()
        repo.export_to_workbook(old, db)
        old['命令'].delete_rows(2, old['命令'].max_row)
        old['节点'].delete_rows(2, old['节点'].max_row)
        old['节点'].append(['start', None, 'start', 0, 0])
        old['节点'].append(['end', None, 'end', 320, 0])
        old['连线'].delete_rows(2, old['连线'].max_row)
        old['连线'].append(['start', 'end', 0])
        for row in old['设置'].iter_rows(min_row=2):
            if row[1].value == '任务名称':
                row[2].value = '过期项目'
        old.save(stale)
        old.close()
        old_bytes = stale.read_bytes()
        new_page = data2 / '空白页2.xlsx'
        cache = window.project_run_controls.cache()
        cache[str(new_page).lower()] = {'运行重复次数': '99', '有限重复次数': '99'}
        db.set_setting_value(CACHE_KEY, json.dumps(cache))
        window.project_run_controls.changed()
        mark_clean(window)
        with patch('anclicker.ui.project_files.QMessageBox.question', return_value=QMessageBox.No):
            assert new_blank_page(window)
        assert db.get_setting_value('当前文件路径') == str(new_page)
        assert not repo.list_commands()
        assert db.get_setting_value('任务名称') == '项目二'
        assert db.get_setting_value('绑定窗口标题') == '目标窗口'
        assert window.project_run_controls.values() == controls
        assert db.extract_resource_folder_path() == saved_resources
        assert stale.read_bytes() == old_bytes
        assert db.get_setting_values(list(global_values)) == global_values
        assert not is_modified(window)

        # Saving an edited blank page does not force a different name or directory.
        repo.append_recording([InstructionDraft('时间等待', {'类型': '时间等待', '时长': 1, '单位': '秒'})])
        with patch('anclicker.app.Start_Win.QFileDialog.getSaveFileName', side_effect=AssertionError('blank page prompted Save As')):
            assert window.save_data('自动保存')
        assert db.get_setting_value('当前文件路径') == str(new_page)
        assert project_directory(DatabaseOperation(db.db_path)) == str(data2)
        book = openpyxl.load_workbook(new_page)
        keys = {row[1] for row in book['设置'].iter_rows(min_row=2, values_only=True)}
        assert not set(global_values).intersection(keys)
        assert not any(row[0] == '窗口大小' for row in book['设置'].iter_rows(min_row=2, values_only=True))
        book.close()

        # Save As may target another folder explicitly; future pages remain in Data2.
        outside = root / '备份.xlsx'
        with patch('anclicker.app.Start_Win.QFileDialog.getSaveFileName', return_value=(str(outside), '')), patch('anclicker.app.Start_Win.QMessageBox.question', return_value=QMessageBox.No):
            assert window.save_data('excel')
        assert project_directory(db) == str(data2)
        assert new_blank_page(window)
        assert Path(db.get_setting_value('当前文件路径')).parent == data2

        # A failed blank-page write must not clear the current in-memory project.
        repo.append_recording([InstructionDraft('时间等待', {'类型': '时间等待', '时长': 2, '单位': '秒'})])
        mark_clean(window)
        before, current = repo.snapshot(), db.get_setting_value('当前文件路径')
        with patch('openpyxl.workbook.workbook.Workbook.save', side_effect=OSError('disk full')), patch('anclicker.ui.project_files.QMessageBox.warning') as warning:
            assert not new_blank_page(window)
            assert warning.called
        assert repo.snapshot() == before and db.get_setting_value('当前文件路径') == current
        assert not (data2 / '空白页4.xlsx').exists()
        window.data_import(str(page))
        assert str(resources) not in db.extract_resource_folder_path()  # no leak from the previous page
        window.data_import(str(outside))
        assert project_directory(db) == str(root)  # explicit open switches projects
        window.close()
        app.processEvents()
    print('PASS root retention, global settings isolation, blank-page parameters/resources, stale-page/cache protection, direct blank save, restart directory, failed-write preservation, explicit project switch')


if __name__ == '__main__':
    with patch('anclicker.app.Start_Win.QMessageBox.warning',
               side_effect=lambda *args: (_ for _ in ()).throw(AssertionError(str(args[1:])))):
        main()
