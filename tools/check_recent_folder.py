"""Verify recent context-menu folder action and error handling."""
from pathlib import Path
import sys
import tempfile
from unittest.mock import patch
sys.path.insert(0,str(Path(__file__).resolve().parents[1]))
from anclicker.platform.qt_compat import configure_application
from anclicker.platform.qt_compat.QtWidgets import QApplication,QWidget,QMenu
from anclicker.platform.qt_compat.QtCore import QPoint
from anclicker.ui.recent_projects import recent_remove_menu,open_recent_folder

def main():
    configure_application()
    app=QApplication.instance() or QApplication([])
    parent=QWidget()
    with tempfile.TemporaryDirectory() as folder:
        path=str(Path(folder)/'文件1.xlsx')
        for choice,remove in [('删除记录',True),('打开所在文件夹',False)]:
            def select(menu,point):
                actions={a.text():a for a in menu.actions()}
                assert set(actions)=={'删除记录','打开所在文件夹','打包为独立运行应用…'}
                return actions[choice]
            with patch.object(QMenu,'exec',select),patch('anclicker.ui.recent_projects.open_path') as opened:
                assert recent_remove_menu(parent,path,QPoint()) is remove
                app.processEvents()
                assert opened.call_count == (0 if remove else 1)
                if not remove:assert Path(opened.call_args.args[0]) == Path(folder)
        Path(path).touch()
        from anclicker.ui.recent_projects import RecentProjectPicker
        picker=RecentProjectPicker(parent)
        for surface in (picker,QMenu(parent)):
            def package(menu,point):
                action=next(a for a in menu.actions() if a.text()=='打包为独立运行应用…')
                assert action.isEnabled()
                return action
            with patch.object(QMenu,'exec',package),patch('anclicker.ui.standalone_export.export_recent_application') as exported:
                assert not recent_remove_menu(surface,path,QPoint())
                assert not exported.called
                app.processEvents()
                exported.assert_called_once_with(surface,path)
        with patch('anclicker.ui.recent_projects.QMessageBox.warning') as warning:
            assert not open_recent_folder(parent,str(Path(folder)/'missing'/'file.xlsx'))
            assert warning.call_count==1
        with patch('anclicker.ui.recent_projects.open_path',side_effect=OSError('failed')),patch('anclicker.ui.recent_projects.QMessageBox.warning') as warning:
            assert not open_recent_folder(parent,path)
            assert warning.call_count==1
    parent.close()
    print('PASS folder action, deletion unchanged, missing directory and open errors')

if __name__=='__main__':main()
