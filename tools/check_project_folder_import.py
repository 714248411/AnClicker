"""Folder import and the shared 20-item recent-project limit."""
from pathlib import Path
import sys,tempfile
from unittest.mock import patch
if __package__ in (None,''):sys.path.insert(0,str(Path(__file__).resolve().parents[1]))
from anclicker.platform.qt_compat import configure_application
from anclicker.platform.qt_compat.QtWidgets import QApplication,QMainWindow,QMenu,QStatusBar
from anclicker.platform.qt_compat.QtGui import QAction
from anclicker.storage.database import DatabaseOperation
from anclicker.app.Start_Win import Main_window
from anclicker.ui.recent_projects import RecentProjectPicker,install_folder_import,import_project_folder

class Host(QMainWindow):
    add_recent_to_fileMenu=Main_window.add_recent_to_fileMenu
    def __init__(self,path):
        super().__init__();self.db=DatabaseOperation(str(path));self.menu=QMenu('文件',self)
        self.actionf=QAction('导入指令',self);self.menu.addAction(self.actionf)
        self.menuzv=QMenu('最近打开',self.menu);self.menu.addMenu(self.menuzv)
        self.statusBar=QStatusBar(self);self.setStatusBar(self.statusBar)
        self.recent_project_picker=RecentProjectPicker(self);self.setCentralWidget(self.recent_project_picker)
        self.opened=[];install_folder_import(self)
    def open_recent_file(self,path):self.opened.append(path)

def main():
    configure_application();app=QApplication.instance() or QApplication([])
    with tempfile.TemporaryDirectory() as folder:
        base=Path(folder);source=base/'批量';source.mkdir();host=Host(base/'task.db')
        for i in range(25):(source/(f'{i:02}流程'+('.XLSM' if i%2 else '.xlsx'))).touch()
        (source/'~$锁定.xlsx').touch();(source/'说明.txt').touch();(source/'旧.xls').touch()
        child=source/'子文件夹';child.mkdir();(child/'不扫描.xlsx').touch()
        current=str(base/'当前项目.xlsx');host.db.set_setting_value('当前文件路径',current)
        actions=host.menu.actions();assert actions[actions.index(host.actionf)+1] is host.action_import_project_folder
        with patch('anclicker.ui.recent_projects.QFileDialog.getExistingDirectory',return_value=str(source)):
            host.action_import_project_folder.trigger()
        expected=sorted([str(p) for p in source.iterdir() if p.suffix.lower() in {'.xlsx','.xlsm'} and not p.name.startswith('~$')])[:20]
        assert host.db.get_recently_opened_file('文件列表')==expected
        assert [a.text() for a in host.menuzv.actions()]==expected
        assert [host.recent_project_picker.combo.itemData(i) for i in range(host.recent_project_picker.combo.count())]==expected
        assert host.recent_project_picker.combo.count()==20
        assert host.db.get_setting_value('当前文件路径')==current
        assert host.db.get_setting_value('最近导入项目文件夹')==str(source)
        with patch('anclicker.ui.recent_projects.QFileDialog.getExistingDirectory',return_value=str(source)) as choose:
            assert import_project_folder(host)==25;assert choose.call_args.args[2]==str(source)
        assert host.db.get_recently_opened_file('文件列表')==expected
        with patch('anclicker.ui.recent_projects.QFileDialog.getExistingDirectory',return_value=''):
            assert import_project_folder(host)==0
        assert host.db.get_recently_opened_file('文件列表')==expected
        with patch('anclicker.ui.recent_projects.QFileDialog.getExistingDirectory',return_value=str(child)):
            assert import_project_folder(host)==1
        values=host.db.get_recently_opened_file('文件列表');assert len(values)==20 and values[0]==str(child/'不扫描.xlsx')
        host.db.writes_to_recently_opened_files(values[-1]);values=host.db.get_recently_opened_file('文件列表')
        assert len(values)==20 and len(set(values))==20
        db=DatabaseOperation(str(base/'task.db'));assert db.get_recently_opened_file('文件列表')==values
        host.add_recent_to_fileMenu();host.menuzv.actions()[0].trigger();assert host.opened[-1]==values[0]
        assert len(host.menuzv.actions())==20 and host.recent_project_picker.combo.count()==20
        data=base/'Data';nested=data/'一级'/'二级';nested.mkdir(parents=True)
        (data/'根.xlsx').touch();(nested/'嵌套.XLSM').touch();(nested/'~$忽略.xlsx').touch()
        with patch('anclicker.app.paths.PORTABLE_DATA_FOLDER',str(data)):
            with patch('anclicker.ui.recent_projects.QFileDialog.getExistingDirectory',return_value=str(data)):
                assert import_project_folder(host)==2
                assert '包含所有子文件夹' in host.statusBar.currentMessage()
            assert str(nested/'嵌套.XLSM') in host.db.get_recently_opened_file('文件列表')
            with patch('anclicker.ui.recent_projects.QFileDialog.getExistingDirectory',return_value=str(data/'一级')):
                assert import_project_folder(host)==0
                assert '仅当前文件夹' in host.statusBar.currentMessage()
        host.close()
    print('PASS folder action immediately below import; mixed XLSX/XLSM; skips locks and subfolders; 25 files retain 20; dedup, cancel, persistence, menu/dropdown sync, current project preserved')
    return 0
if __name__=='__main__':raise SystemExit(main())
