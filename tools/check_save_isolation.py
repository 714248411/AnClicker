"""Real workbook regressions for overwrite consent, numbering and project isolation."""
from pathlib import Path
import sys
import tempfile
from unittest.mock import patch
import openpyxl
if __package__ in (None, ''):
    sys.path.insert(0, str(Path(__file__).resolve().parents[1]))
from anclicker.platform.qt_compat.QtWidgets import QApplication, QMessageBox, QPlainTextEdit, QLabel
from anclicker.domain.instructions import InstructionDraft
from anclicker.ui.project_files import PROJECT_DIRECTORY, new_blank_page
from anclicker.ui.project_changes import mark_clean
from anclicker.ui.recent_projects import import_project_folder
from anclicker.ui.code_workspace import CodeWorkspace
from anclicker.ui.workspace_constants import CODE_SETTING, CODE_GRAPH_SIGNATURE_SETTING
from tools.check_xlsm_drop import DropHost


class View:
    pass


def main():
    app = QApplication.instance() or QApplication([])
    with tempfile.TemporaryDirectory() as directory:
        root = Path(directory)
        data = root / 'Data'
        data2 = root / 'Data2'
        data.mkdir()
        data2.mkdir()
        window = DropHost(data / 'task.db')
        repo = window.workspace.repository
        repo.append_recording([InstructionDraft('时间等待', {'类型': '时间等待', '时长': 0, '单位': '秒'})])
        source = data / '项目009.xlsx'
        window.db.set_setting_value('当前文件路径', str(source))
        with patch('anclicker.app.Start_Win.QFileDialog.getSaveFileName', side_effect=AssertionError('direct save prompted')):
            assert window.save_data('自动保存')
            repo.append_recording([InstructionDraft('时间等待', {'类型': '时间等待', '时长': 1, '单位': '秒'})])
            assert window.save_data('自动保存')
        original = source.read_bytes()
        occupied = data / '项目010.xlsx'
        occupied.write_bytes(b'untouched sibling')
        target = data / '项目011.xlsx'
        with patch('anclicker.app.Start_Win.QFileDialog.getSaveFileName', return_value=(str(target), '')) as choose, patch('anclicker.app.Start_Win.QMessageBox.question', return_value=QMessageBox.No):
            assert window.save_data('excel')
            assert choose.call_args.args[2] == str(target)
        assert source.read_bytes() == original and occupied.read_bytes() == b'untouched sibling'

        # Normalize the extension before asking; cancellation must preserve files and identity.
        current = window.db.get_setting_value('当前文件路径')
        with patch('anclicker.app.Start_Win.QFileDialog.getSaveFileName', return_value=(str(source.with_suffix('')), '')), patch('anclicker.app.Start_Win.QMessageBox.question', return_value=QMessageBox.No) as ask:
            assert not window.save_data('excel')
            assert ask.call_count == 1 and str(source) in ask.call_args.args[2]
        assert source.read_bytes() == original and window.db.get_setting_value('当前文件路径') == current
        with patch('anclicker.app.Start_Win.QFileDialog.getSaveFileName', return_value=(str(source), '')), patch('anclicker.app.Start_Win.QMessageBox.question', side_effect=[QMessageBox.Yes, QMessageBox.No]) as ask:
            assert window.save_data('excel')
            assert sum(call.args[1] == '确认覆盖' for call in ask.call_args_list) == 1

        # A macro source and its same-stem XLSX never silently overwrite each other.
        macro = data2 / '同名.xlsm'
        macro.write_bytes(b'original macro workbook')
        sibling = data2 / '同名.xlsx'
        sibling.write_bytes(b'original xlsx workbook')
        (data2 / '同名1.xlsx').write_bytes(b'number one')
        window.db.set_setting_values({'当前文件路径': str(macro), PROJECT_DIRECTORY: str(data2)})
        macro_target = data2 / '同名2.xlsx'
        with patch('anclicker.app.Start_Win.QFileDialog.getSaveFileName', return_value=(str(macro_target), '')) as choose:
            assert window.save_data('自动保存')
            assert choose.call_args.args[2] == str(macro_target)
        assert macro.read_bytes() == b'original macro workbook' and sibling.read_bytes() == b'original xlsx workbook'
        saved = openpyxl.load_workbook(macro_target)
        repo.validate_workbook(saved)
        assert PROJECT_DIRECTORY not in {row[1] for row in saved['设置'].iter_rows(min_row=2, values_only=True)}
        saved.close()

        # Existing-file save failure leaves both the previous workbook and current path intact.
        before = macro_target.read_bytes()
        with patch('anclicker.app.Start_Win.os.replace', side_effect=PermissionError('locked')), patch('anclicker.app.Start_Win.QMessageBox.critical'):
            assert not window.save_data('自动保存')
        assert macro_target.read_bytes() == before
        assert window.db.get_setting_value('当前文件路径') == str(macro_target)
        assert not list(data2.glob('.yanyi-*'))

        # File creation after the chooser is also protected by an overwrite prompt.
        raced = data2 / 'race.xlsx'
        original_export = repo.export_to_workbook
        def export_and_race(*args, **kwargs):
            original_export(*args, **kwargs)
            raced.write_bytes(b'created by another writer')
        with patch('anclicker.app.Start_Win.QFileDialog.getSaveFileName', return_value=(str(raced), '')), patch.object(repo, 'export_to_workbook', side_effect=export_and_race), patch('anclicker.app.Start_Win.QMessageBox.question', return_value=QMessageBox.No) as ask:
            assert not window.save_data('excel')
            assert ask.call_count == 1
        assert raced.read_bytes() == b'created by another writer'
        assert window.db.get_setting_value('当前文件路径') == str(macro_target)

        # Selecting Data2 affects the next new project, even while a Data project is active.
        window.db.set_setting_value('当前文件路径', str(source))
        with patch('anclicker.ui.recent_projects.QFileDialog.getExistingDirectory', return_value=str(data2)):
            import_project_folder(window)
        mark_clean(window)
        repo.append_recording([InstructionDraft('时间等待', {'类型': '时间等待', '时长': 2, '单位': '秒'})])
        with patch('anclicker.ui.project_files.QMessageBox.question', return_value=QMessageBox.Yes):
            assert new_blank_page(window)
        assert Path(window.db.get_setting_value('当前文件路径')).parent == data2

        # Identical graphs with different custom code must reload the chosen file's editor.
        view = View()
        view.__dict__.update(vars(window.view_workspace))
        view.window = window
        window.view_workspace = view
        view.code_editor = QPlainTextEdit()
        view.code_status = QLabel()
        controller = CodeWorkspace(view)
        view._current_graph_state = lambda: (repo.snapshot(), None)
        view._graph_signature = CodeWorkspace._graph_signature
        view._generated_code = controller._generated_code
        view._load_code = controller._load_code
        view._save_code = controller._save_code
        view.refresh_all = lambda: controller._sync_code_if_needed()
        a, b = data2 / 'code.xlsx', data2 / 'code.xlsm'
        for path, code in ((a, 'print("A")'), (b, 'print("B")')):
            window.db.set_setting_values({CODE_SETTING: code, CODE_GRAPH_SIGNATURE_SETTING: view._graph_signature(repo.snapshot())})
            book = openpyxl.Workbook()
            repo.export_to_workbook(book, window.db)
            # Old exports may contain another machine's local directories: ignore them.
            book['设置'].append(['设置', PROJECT_DIRECTORY, str(data), '其他', None])
            book['设置'].append(['设置', '当前文件路径', str(source), '其他', None])
            book.save(path)
            book.close()
        for path, code in ((a, 'print("A")'), (b, 'print("B")'), (a, 'print("A")')):
            view.code_editor.setPlainText('stale previous project')
            view._code_dirty = True
            view._code_save_timer.start(10)
            window.data_import(str(path))
            app.processEvents()
            assert view.code_editor.toPlainText() == code
            view._save_code()
            assert window.db.get_setting_value(CODE_SETTING) == code
            assert window.db.get_setting_value('当前文件路径') == str(path)
            assert window.db.get_setting_value(PROJECT_DIRECTORY) == str(data2)
        minimal = data2 / 'minimal.xlsx'
        book = openpyxl.load_workbook(a)
        for row in range(book['设置'].max_row, 1, -1):
            if book['设置'].cell(row, 1).value == '设置':
                book['设置'].delete_rows(row)
        book.save(minimal)
        book.close()
        window.data_import(str(minimal))
        assert window.db.get_setting_value('任务名称') == '默认任务'
        assert window.db.get_setting_value('绑定窗口标题') == ''
        assert window.db.get_setting_value(CODE_SETTING) not in ('print("A")', 'print("B")')
        window.close()
    print('PASS direct save, numbered Save As, explicit overwrite/cancel, extension normalization, XLSM sibling isolation, atomic failure, racing creation, Data2 new project, code switching')


if __name__ == '__main__':
    main()
