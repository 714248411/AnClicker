"""New blank projects immediately appear in both recent surfaces."""
from pathlib import Path
import sys
import tempfile
from types import SimpleNamespace
from unittest.mock import Mock
sys.path.insert(0,str(Path(__file__).resolve().parents[1]))
from tools.check_new_blank_164 import Host
from anclicker.app.Start_Win import Main_window
from anclicker.platform.qt_compat import configure_application
from anclicker.platform.qt_compat.QtWidgets import QApplication,QMenu,QWidget,QVBoxLayout
from anclicker.platform.qt_compat.QtCore import Qt
from anclicker.ui.home_workspace import HomeWorkspace
from anclicker.ui.recent_projects import RecentProjectPicker
from anclicker.ui.project_files import new_blank_page

def main():
    configure_application()
    app=QApplication.instance() or QApplication([])
    with tempfile.TemporaryDirectory() as folder:
        base=Path(folder)
        window=Host(base/'task.db')
        window.menuzv=QMenu(window)
        window.recent_project_picker=RecentProjectPicker(window)
        def card(*args):
            widget=QWidget()
            return widget,QVBoxLayout(widget)
        view=window.view_workspace
        view.window=window
        view._card=card
        for name in ('show_table','show_flow','show_code','show_recording','show_web_recording','show_variables'):
            setattr(view,name,lambda:None)
        view.main_page=HomeWorkspace(view)
        view.main_page.show()
        app.processEvents()
        window.add_recent_to_fileMenu=Main_window.add_recent_to_fileMenu.__get__(window)
        window.db.set_setting_value('当前文件路径',str(base/'old.xlsx'))
        assert new_blank_page(window)
        path=window.db.get_setting_value('当前文件路径')
        assert Path(path).name=='空白页1.xlsx'
        assert view.main_page.recent.currentItem().data(Qt.UserRole)==path
        assert window.recent_project_picker.combo.currentData()==path
        assert any(a.data()==path for a in window.menuzv.actions())
        first=path
        assert new_blank_page(window)
        assert window.db.get_setting_value('当前文件路径')==first
        assert window.recent_project_picker.combo.count()==1
        from anclicker.domain.instructions import InstructionDraft
        from anclicker.platform.qt_compat.QtWidgets import QMessageBox
        from unittest.mock import patch
        window.workspace.repository.append_recording([InstructionDraft('时间等待',{'类型':'时间等待','时长':0,'单位':'秒'})])
        with patch('anclicker.ui.project_files.QMessageBox.question', return_value=QMessageBox.No):
            assert new_blank_page(window)
        path=window.db.get_setting_value('当前文件路径')
        assert Path(path).name=='空白页2.xlsx'
        assert {first,path}.issubset({a.data() for a in window.menuzv.actions()})
        assert window.recent_project_picker.combo.count()==2
        assert view.main_page.recent.count()==2
        (base/'空白页4.xlsx').write_bytes(b'existing')
        assert new_blank_page(window)
        path=window.db.get_setting_value('当前文件路径')
        assert Path(path).name=='空白页5.xlsx'
        assert window.recent_project_picker.combo.count()==3
        assert len(window.menuzv.actions())==3
        assert view.main_page.recent.count()==3
        assert view.main_page.recent.currentItem().data(Qt.UserRole)==path
        assert window.recent_project_picker.combo.currentData()==path
        # Switching away still reuses the last empty workbook on disk.
        from anclicker.ui.project_changes import mark_clean
        window.db.set_setting_value('当前文件路径',str(base/'other.xlsx'))
        mark_clean(window)
        def imported(target):
            window.db.set_setting_value('当前文件路径',target)
            mark_clean(window)
        window.data_import=Mock(side_effect=imported)
        before=set(base.glob('*.xlsx'))
        assert new_blank_page(window)
        window.data_import.assert_called_once()
        assert Path(window.data_import.call_args.args[0])==Path(path)
        assert set(base.glob('*.xlsx'))==before
        # Different slash/case spelling must still select the actual recent entry.
        alias=path.replace('\\','/').upper()
        window.db.set_setting_value('当前文件路径',alias)
        window.add_recent_to_fileMenu()
        app.processEvents()
        assert window.recent_project_picker.combo.currentData()==path
        assert view.main_page.recent.currentItem().data(Qt.UserRole)==path
        view.main_page.close()
        window.close()
    print('PASS blank appears immediately in recent menu and picker, home refreshed, empty page reused in memory and on disk, edited page increments')

if __name__=='__main__':main()
