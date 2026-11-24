"""Regression: XLSM drops import a project without modifying or executing macros."""
from pathlib import Path
import sys,tempfile,zipfile
from types import SimpleNamespace
from unittest.mock import patch
import openpyxl
if __package__ in (None,''):sys.path.insert(0,str(Path(__file__).resolve().parents[1]))
from anclicker.platform.qt_compat import configure_application
from anclicker.platform.qt_compat.QtCore import QMimeData,QUrl,Qt,QPoint,QPointF
from anclicker.platform.qt_compat.QtGui import QDragEnterEvent,QDropEvent
from anclicker.platform.qt_compat.QtWidgets import QApplication,QMenu,QMessageBox
from anclicker.app.Start_Win import Main_window
from anclicker.domain.instructions import InstructionDraft
from anclicker.ui.recent_projects import dropped_project,ProjectDropFilter
from tools.check_new_blank_164 import Host

class DropHost(Host):
    data_import=Main_window.data_import
    def __init__(self,path):
        super().__init__(path);self.menuzv=QMenu(self);self.workspace.reload_graph=lambda *args,**kwargs:None

def mime_for(*paths):
    mime=QMimeData();mime.setUrls([QUrl.fromLocalFile(str(path)) for path in paths]);return mime

def main():
    configure_application();app=QApplication.instance() or QApplication([])
    with tempfile.TemporaryDirectory() as folder:
        folder=Path(folder);host=DropHost(folder/'task.db');repo=host.workspace.repository
        repo.append_recording([InstructionDraft('时间等待',{'类型':'时间等待','时长':0,'单位':'秒'})])
        book=openpyxl.Workbook();repo.export_to_workbook(book,host.db);xlsx=folder/'正常项目.xlsx';book.save(xlsx);book.close()
        macro=folder/'宏项目.XLSM'
        with zipfile.ZipFile(xlsx) as source,zipfile.ZipFile(macro,'w') as output:
            for item in source.infolist():
                data=source.read(item.filename)
                if item.filename=='[Content_Types].xml':
                    data=data.replace(b'application/vnd.openxmlformats-officedocument.spreadsheetml.sheet.main+xml',b'application/vnd.ms-excel.sheet.macroEnabled.main+xml')
                output.writestr(item,data)
            output.writestr('xl/vbaProject.bin',b'INERT MACRO FIXTURE - MUST NEVER EXECUTE')
        original=macro.read_bytes();assert dropped_project(mime_for(macro))==str(macro)
        assert dropped_project(mime_for(xlsx))==str(xlsx)
        assert dropped_project(mime_for(xlsx,macro)) is None
        assert dropped_project(mime_for(folder/'missing.xlsm')) is None
        wrong=folder/'wrong.xls';wrong.write_bytes(b'not supported');assert dropped_project(mime_for(wrong)) is None
        remote=QMimeData();remote.setUrls([QUrl('https://example.com/project.xlsm')]);assert dropped_project(remote) is None
        internal=QMimeData();internal.setData('application/x-anclicker-instruction',b'{}');assert dropped_project(internal) is None
        repo.clear();drop_filter=ProjectDropFilter(host,host.data_import);host.show();app.processEvents()
        with patch('anclicker.app.Start_Win.QMessageBox.warning') as warning:
            mime=mime_for(macro);enter=QDragEnterEvent(QPoint(20,20),Qt.CopyAction,mime,Qt.LeftButton,Qt.NoModifier)
            assert QApplication.sendEvent(host,enter) and enter.isAccepted()
            drop=QDropEvent(QPointF(20,20),Qt.CopyAction,mime,Qt.LeftButton,Qt.NoModifier)
            QApplication.sendEvent(host,drop);app.processEvents()
            assert drop.isAccepted() and not warning.called,warning.call_args
        assert len(repo.list_commands())==1 and host.db.get_setting_value('当前文件路径')==str(macro)
        repo.clear()
        with patch('anclicker.app.Start_Win.QFileDialog.getOpenFileName',return_value=(str(macro),'')) as choose,patch('anclicker.app.Start_Win.QMessageBox.information'):
            host.data_import('资源文件夹路径');assert '*.xlsm' in choose.call_args.args[3]
        assert len(repo.list_commands())==1
        snapshot=repo.snapshot();bad=folder/'普通表格.xlsm';book=openpyxl.Workbook();book.save(bad);book.close()
        with patch('anclicker.app.Start_Win.QMessageBox.warning') as warning:
            host.data_import(str(bad));assert warning.called
        assert repo.snapshot()==snapshot
        with patch('anclicker.app.Start_Win.QFileDialog.getSaveFileName',return_value=('','')):
            assert not host.save_data('自动保存')
        assert host.db.get_setting_value('当前文件路径')==str(macro)
        target=folder/'宏项目1.xlsx'
        with patch('anclicker.app.Start_Win.QFileDialog.getSaveFileName',return_value=(str(target),'')) as choose:
            assert host.save_data('自动保存');assert choose.call_args.args[2]==str(target)
        assert macro.read_bytes()==original
        saved=openpyxl.load_workbook(target);repo.validate_workbook(saved);saved.close()
        assert not (folder/'宏项目.XLSM.xlsx').exists()
        app.removeEventFilter(drop_filter);host.close()
    print('PASS XLSM real Qt drag/drop and file-dialog import; uppercase extension; invalid workbook rollback; XLSX compatibility; macro source unchanged; save-as and cancellation')
    return 0
if __name__=='__main__':raise SystemExit(main())
