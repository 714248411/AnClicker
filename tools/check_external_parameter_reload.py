"""External edits to 参数JSON must survive reopening the current workbook."""
import json
from pathlib import Path
import sys
import tempfile
from types import SimpleNamespace
from unittest.mock import patch
import openpyxl
if __package__ in (None,''):sys.path.insert(0,str(Path(__file__).resolve().parents[1]))
from anclicker.app.Start_Win import Main_window
from anclicker.domain.instructions import InstructionDraft, ExecutionContext
from anclicker.instructions.等待.时间等待.executor import InstructionExecutor
from anclicker.ui.instruction_editors.等待.时间等待 import InstructionEditor
from anclicker.platform.qt_compat import configure_application
from anclicker.platform.qt_compat.QtWidgets import QApplication, QMessageBox
from anclicker.ui.recent_projects import RecentProjectPicker
from tools.check_xlsm_drop import DropHost


class ReloadHost(DropHost):
    open_project_path=Main_window.open_project_path
    open_recent_file=Main_window.open_recent_file
    def __init__(self,path):
        super().__init__(path)
        self.view_workspace.recording_page=SimpleNamespace(busy=False,drafts=[],written=True)


def main():
    configure_application();app=QApplication.instance() or QApplication([])
    with tempfile.TemporaryDirectory() as directory:
        folder=Path(directory);host=ReloadHost(folder/'task.db');repo=host.workspace.repository
        repo.append_recording([InstructionDraft('时间等待',{'类型':'时间等待','时长':1,'单位':'秒'})])
        file=folder/'流程.xlsx';book=openpyxl.Workbook();repo.export_to_workbook(book,host.db);book.save(file);book.close()
        host.data_import(str(file))
        book=openpyxl.load_workbook(file);book['命令']['C2']=json.dumps({'类型':'时间等待','时长':7.5,'单位':'秒'},ensure_ascii=False);book.save(file);book.close()
        latest=file.read_bytes();before=repo.snapshot()
        with patch('anclicker.app.Start_Win.QMessageBox.question',return_value=QMessageBox.No):
            host.open_project_path(str(file))
        assert repo.snapshot()==before and file.read_bytes()==latest
        picker=RecentProjectPicker(host);picker.openRequested.connect(host.open_project_path);picker.refresh([str(file)],str(file))
        with patch('anclicker.app.Start_Win.QMessageBox.question',return_value=QMessageBox.Yes) as question,patch.object(host,'save_data',side_effect=AssertionError('stale task must not overwrite workbook')):
            picker._activated(0)
        assert question.call_args.args[1]=='重新打开项目'
        command=repo.list_commands()[0];assert command.parameters['时长']==7.5,command
        editor=InstructionEditor(draft=InstructionDraft(command.type_id,command.parameters))
        assert editor._controls['时长'].value()==7.5
        assert editor.get_draft().parameters['时长']==7.5
        waits=[];context=ExecutionContext(metadata={'wait_interruptibly':lambda seconds,context:waits.append(seconds) or True})
        runtime=repo.execution_snapshot();record=next(command for command in runtime.commands if command.type_id=='时间等待')
        InstructionExecutor().execute_once(context,record)
        assert waits==[7.5],waits
        assert file.read_bytes()==latest
        with patch('anclicker.app.Start_Win.QMessageBox.question',return_value=QMessageBox.Yes),patch.object(host,'data_import',wraps=host.data_import) as load:
            host.open_recent_file(str(file))
            load.assert_called_once_with(str(file))
        print('PASS File > recent also reloads the current path',flush=True)
        print('PASS same-path recent selection rereads edited JSON; editor and runtime use 7.5 instead of 1; source is unchanged',flush=True)
        editor.close()
        book=openpyxl.load_workbook(file);book['命令']['C2']='{invalid json';book.save(file);book.close()
        before=repo.snapshot();invalid=file.read_bytes()
        with patch('anclicker.app.Start_Win.QMessageBox.question',return_value=QMessageBox.Yes),patch('anclicker.app.Start_Win.QMessageBox.warning') as warning:
            host.open_project_path(str(file))
        assert warning.called and repo.snapshot()==before and file.read_bytes()==invalid
        print('PASS cancelling reload preserves edits; malformed JSON fails visibly and preserves loaded project',flush=True)
        host.close()
    return 0


if __name__=='__main__':raise SystemExit(main())
