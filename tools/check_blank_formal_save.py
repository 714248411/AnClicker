"""Formal save uses instruction-data name; cancellation retains blank draft."""
from pathlib import Path
import sys
import tempfile
from unittest.mock import patch
sys.path.insert(0,str(Path(__file__).resolve().parents[1]))
from tools.check_new_blank_164 import Host
from anclicker.platform.qt_compat import configure_application
from anclicker.platform.qt_compat.QtWidgets import QApplication
from anclicker.ui.project_files import new_blank_page

def main():
    configure_application()
    app=QApplication.instance() or QApplication([])
    with tempfile.TemporaryDirectory() as folder:
        base=Path(folder)
        window=Host(base/'task.db')
        window.db.set_setting_value('当前文件路径',str(base/'old.xlsx'))
        assert new_blank_page(window)
        draft=base/'空白页1.xlsx'
        original=draft.read_bytes()
        (base/'指令数据1.xlsx').write_bytes(b'existing')
        with patch('anclicker.app.Start_Win.QFileDialog.getSaveFileName') as chooser:
            assert window.save_data('自动保存')
            assert not chooser.called
        original=draft.read_bytes()
        for mode in ('新建前另存为',):
            with patch('anclicker.app.Start_Win.QFileDialog.getSaveFileName',return_value=('','')) as chooser:
                assert not window.save_data(mode)
                assert Path(chooser.call_args.args[2])==base/'指令数据2.xlsx'
                assert Path(window.db.get_setting_value('当前文件路径'))==draft
        target=base/'指令数据2.xlsx'
        with patch('anclicker.app.Start_Win.QFileDialog.getSaveFileName',return_value=(str(target),'')):
            assert window.save_data('新建前另存为')
        assert target.is_file()
        recent=window.db.get_recently_opened_file('文件列表')
        assert str(draft) not in recent
        assert str(target) in recent
        assert Path(window.db.get_setting_value('当前文件路径'))==target
        assert draft.read_bytes()==original
        assert (base/'指令数据1.xlsx').read_bytes()==b'existing'
        with patch('anclicker.app.Start_Win.QFileDialog.getSaveFileName') as chooser:
            assert window.save_data('自动保存')
            assert not chooser.called
        window.close()
    print('PASS blank draft, formal save default, collision, cancellation, subsequent direct save')

if __name__=='__main__':main()
