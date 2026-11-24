"""Check that each new blank project is saved under an unused incremented name."""
from pathlib import Path
import sys
import tempfile
from unittest.mock import patch
import openpyxl
sys.path.insert(0, str(Path(__file__).resolve().parents[1]))
from tools.check_new_blank_164 import Host
from anclicker.platform.qt_compat import configure_application
from anclicker.platform.qt_compat.QtWidgets import QApplication
from anclicker.ui.project_files import NEW_PROJECT_PATH, next_project_path, new_blank_page
from anclicker.ui.project_changes import is_modified, mark_clean


def main():
    configure_application()
    app = QApplication.instance() or QApplication([])
    with tempfile.TemporaryDirectory() as folder:
        base = Path(folder)
        assert Path(next_project_path(base/'任务.xlsx')).name == '任务1.xlsx'
        assert Path(next_project_path(base/'任务009.xlsm')).name == '任务010.xlsx'
        old = base/'任务1.xlsx'
        old.write_bytes(b'keep original')
        (base/'任务2.xlsx').write_bytes(b'keep second')
        (base/'空白页1.xlsx').write_bytes(b'blank one')
        (base/'空白页2.xlsx').write_bytes(b'blank two')
        (base/'空白页4.xlsx').write_bytes(b'blank four')
        (base/'任务4.xlsx').write_bytes(b'keep fourth')
        window = Host(base/'task.db')
        window.db.set_setting_value('当前文件路径', str(base/'任务4.xlsx'))
        with patch('anclicker.app.Start_Win.QFileDialog.getSaveFileName') as chooser, patch('anclicker.ui.project_files.QMessageBox.question') as question:
            for number in (5, 6):
                window.db.set_setting_value('当前文件路径', str(old))
                mark_clean(window)
                assert new_blank_page(window)
                target = base/f'空白页{number}.xlsx'
                assert Path(window.db.get_setting_value('当前文件路径')) == target
                assert target.exists()
                workbook = openpyxl.load_workbook(target)
                workbook.close()
                assert not window.workspace.repository.list_commands()
                assert not is_modified(window)
            assert not chooser.called and not question.called
        # Recheck collisions at the actual save step too.
        window.db.set_setting_value(NEW_PROJECT_PATH, str(base/'空白页6.xlsx'))
        assert window.save_data('保存新空白页')
        assert Path(window.db.get_setting_value('当前文件路径')) == base/'空白页7.xlsx'
        assert old.read_bytes() == b'keep original'
        assert (base/'任务4.xlsx').read_bytes() == b'keep fourth'
        assert Path(next_project_path(base/'空白页10.xlsx', fill_gaps=True)).name == '空白页3.xlsx'
        assert (base/'空白页4.xlsx').read_bytes() == b'blank four'
        assert (base/'任务2.xlsx').read_bytes() == b'keep second'
        assert not window.db.get_setting_value(NEW_PROJECT_PATH)
        window.close()
    print('PASS automatic blank save, repeated new, clean baseline, increment, existing files preserved')

if __name__ == '__main__':
    main()
