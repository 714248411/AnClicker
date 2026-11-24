"""Missing recent files share one notice and never switch or save the workspace."""
from pathlib import Path
import sys
import tempfile
from types import SimpleNamespace
from unittest.mock import Mock, patch
sys.path.insert(0, str(Path(__file__).resolve().parents[1]))
from tools.check_new_blank_164 import Host
from anclicker.app.Start_Win import Main_window
from anclicker.platform.qt_compat import configure_application
from anclicker.platform.qt_compat.QtWidgets import QApplication


def main():
    configure_application()
    app = QApplication.instance() or QApplication([])
    with tempfile.TemporaryDirectory() as folder:
        base = Path(folder)
        window = Host(base/'task.db')
        window.open_project_path = Main_window.open_project_path.__get__(window)
        window.open_recent_file = Main_window.open_recent_file.__get__(window)
        window.view_workspace.main_page = SimpleNamespace(refresh_projects=Mock())
        window.data_import = Mock()
        window.save_data = Mock()
        current = str(base/'current.xlsx')
        window.db.set_setting_value('当前文件路径', current)
        notices = []
        for opener in (window.open_project_path, window.open_recent_file):
            missing = str(base/'missing.xlsx')
            window.db.writes_to_recently_opened_files(missing)
            with patch('anclicker.app.Start_Win.QMessageBox.critical') as notice, patch('anclicker.app.Start_Win.QMessageBox.question') as question:
                opener(missing)
                assert notice.call_count == 1
                notices.append(notice.call_args.args[1:])
                assert not question.called
            assert missing not in window.db.get_recently_opened_file('文件列表')
            assert window.db.get_setting_value('当前文件路径') == current
        assert notices[0] == notices[1]
        assert window.view_workspace.main_page.refresh_projects.call_count == 2
        assert not window.data_import.called and not window.save_data.called
        window.close()
    print('PASS identical missing-file notices, recent removal, refreshed lists, active project preserved')

if __name__ == '__main__':
    main()
