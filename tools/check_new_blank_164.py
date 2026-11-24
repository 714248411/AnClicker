"""Check File > New with real workbook save, cancel and failure paths."""
from pathlib import Path
import sys
import tempfile
from types import SimpleNamespace
from unittest.mock import patch
import openpyxl

if __package__ in (None,''):
    sys.path.insert(0,str(Path(__file__).resolve().parents[1]))
from anclicker.platform.qt_compat import configure_application
from anclicker.platform.qt_compat.QtCore import QTimer
from anclicker.platform.qt_compat.QtWidgets import QApplication,QMainWindow,QMenu,QStatusBar,QLineEdit,QMessageBox
from anclicker.app.Start_Win import Main_window
from anclicker.domain.instructions import InstructionDraft
from anclicker.storage.database import DatabaseOperation
from anclicker.storage.graph_repository import GraphRepository,START_NODE_ID,END_NODE_ID
from anclicker.ui.project_files import install_new_blank_action,new_blank_page
from anclicker.ui.project_changes import mark_clean


class Workspace:
    def __init__(self,repository):self.repository=repository;self.history_cleared=False
    def clear(self,confirm=True):self.repository.clear();return True
    def clear_connection_history(self):self.history_cleared=True
    def reload_graph(self, *args, **kwargs):pass


class Host(QMainWindow):
    save_data=Main_window.save_data
    data_import=Main_window.data_import
    def __init__(self,path):
        super().__init__();self.db=DatabaseOperation(str(path));self.workspace=Workspace(GraphRepository(str(path)))
        self.statusBar=QStatusBar(self);self.setStatusBar(self.statusBar)
        self.menu=QMenu('文件',self);self.menu.addAction('另存为');self.refreshes=0
        self.menuzv=QMenu('最近打开',self)
        self.view_workspace=SimpleNamespace(_code_save_timer=QTimer(self),_code_dirty=True,task_name=QLineEdit('旧任务'),window_title=QLineEdit('旧窗口'),
            _save_code=lambda:None,_sync_code_if_needed=lambda **kw:None,refresh_all=lambda:None)
        self.command_thread=SimpleNamespace(isRunning=lambda:False)
        install_new_blank_action(self)
    def add_recent_to_fileMenu(self):self.refreshes+=1


def main():
    configure_application();app=QApplication.instance() or QApplication([])
    with tempfile.TemporaryDirectory() as folder:
        path=Path(folder);window=Host(path/'task.db');repo=window.workspace.repository
        assert window.menu.actions()[0] is window.action_new_blank
        assert window.action_new_blank.shortcut().toString()=='Ctrl+N'
        window.db.set_setting_value('当前文件路径',str(path/'blank.xlsx'))
        with patch('anclicker.ui.project_files.QMessageBox.question') as question:
            window.action_new_blank.trigger();assert not question.called
        assert not repo.list_commands()
        draft=InstructionDraft('时间等待',{'类型':'时间等待','时长':0,'单位':'秒'})
        def fill():
            repo.append_recording([draft]);window.db.set_setting_values({'当前文件路径':str(path/'文件4.xlsx'),'任务名称':'旧任务','多功能代码':'旧代码'})
            window.view_workspace._code_dirty=True;window.view_workspace._code_save_timer.start(10000)
        fill();before=repo.snapshot()
        with patch('anclicker.ui.project_files.QMessageBox.question',return_value=QMessageBox.Cancel):
            assert not new_blank_page(window)
        assert repo.snapshot()==before and window.db.get_setting_value('当前文件路径')==str(path/'文件4.xlsx')
        with patch('anclicker.ui.project_files.QMessageBox.question',return_value=QMessageBox.Yes),patch('anclicker.app.Start_Win.QFileDialog.getSaveFileName',return_value=(str(path/'saved.xlsx'),'')),patch.object(repo,'export_to_workbook',side_effect=OSError('模拟保存失败')),patch('anclicker.app.Start_Win.QMessageBox.warning'):
            assert not new_blank_page(window)
        assert repo.snapshot()==before
        original=path/'文件4.xlsx';original.write_bytes(b'original stays unchanged')
        with patch('anclicker.ui.project_files.QMessageBox.question',return_value=QMessageBox.Yes) as question,patch('anclicker.app.Start_Win.QFileDialog.getSaveFileName',return_value=(str(path/'saved.xlsx'),'')) as chooser:
            assert new_blank_page(window)
            assert question.call_count==1 and not chooser.called
            assert '文件4.xlsx' in question.call_args.args[2]
            assert not (path/'文件5.xlsx').exists()
        assert original.read_bytes()!=b'original stays unchanged'
        workbook=openpyxl.load_workbook(original);assert len(workbook.worksheets[0]['A'])>=2;workbook.close()
        assert not repo.list_commands() and window.workspace.history_cleared
        snapshot=repo.snapshot();assert {(edge.source,edge.target) for edge in snapshot.edges}=={(START_NODE_ID,END_NODE_ID)}
        assert Path(window.db.get_setting_value('当前文件路径'))==path/'空白页2.xlsx' and window.db.get_setting_value('多功能代码')==''
        assert not window.view_workspace._code_save_timer.isActive() and not window.view_workspace._code_dirty
        fill()
        with patch('anclicker.ui.project_files.QMessageBox.question',return_value=QMessageBox.No),patch('anclicker.app.Start_Win.QFileDialog.getSaveFileName') as chooser:
            assert new_blank_page(window);assert not chooser.called
        assert not repo.list_commands()
        # Saved content, even with commands, must open a blank page without prompting.
        fill();mark_clean(window)
        with patch('anclicker.ui.project_files.QMessageBox.question') as question:
            assert new_blank_page(window)
            assert not question.called
        # Deleting all commands is still a change and must prompt.
        fill();mark_clean(window);repo.clear()
        with patch('anclicker.ui.project_files.QMessageBox.question',return_value=QMessageBox.No) as question:
            assert new_blank_page(window)
            assert question.call_count == 1
        # Settings-only edits also count as unsaved changes.
        window.db.set_setting_value('任务名称', '改过的任务')
        with patch('anclicker.ui.project_files.QMessageBox.question',return_value=QMessageBox.No) as question:
            assert new_blank_page(window)
            assert question.call_count == 1
        fill();window.command_thread=SimpleNamespace(isRunning=lambda:True)
        with patch('anclicker.ui.project_files.QMessageBox.question') as question:
            assert not new_blank_page(window);assert not question.called
        assert repo.list_commands()
        window.close()
    print('PASS File menu/shortcut, empty task, Yes updates current file then clears, No clears, cancel/save failure preserve task, active-task guard')
    return 0

if __name__=='__main__':raise SystemExit(main())
