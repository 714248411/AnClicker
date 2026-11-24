"""Project switching restores controls and only prompts for changed content."""
import os,sys,tempfile,json
from pathlib import Path
from types import SimpleNamespace
from unittest.mock import patch
sys.path.insert(0,str(Path(__file__).resolve().parents[1]))
os.environ['QT_QPA_PLATFORM']='offscreen'
import openpyxl
from anclicker.platform.qt_compat.QtWidgets import QApplication,QRadioButton,QSpinBox,QCheckBox,QMessageBox
from anclicker.app.Start_Win import Main_window
from anclicker.ui.project_run_controls import ProjectRunControls, CACHE_KEY
from anclicker.ui.project_changes import mark_clean,is_modified
from anclicker.domain.instructions import InstructionDraft
from tools.check_xlsm_drop import DropHost

class Host(DropHost):
    open_project_path=Main_window.open_project_path
    def __init__(self,path):
        super().__init__(path)
        self.workspace.reload_graph=lambda *a,**kw:None
        self.radioButton=QRadioButton(self);self.radioButton_2=QRadioButton(self)
        self.spinBox=QSpinBox(self);self.spinBox.setRange(1,99999)
        self.run_unconnected_checkbox=QCheckBox(self);self.checkBox_2=QCheckBox(self)
        self.view_workspace.recording_page=SimpleNamespace(busy=False,drafts=[],written=True)
        self.project_run_controls=ProjectRunControls(self)

app=QApplication.instance() or QApplication([])
with tempfile.TemporaryDirectory() as directory:
    folder=Path(directory)
    w=Host(folder/'db.sqlite')
    repo=w.workspace.repository
    repo.append_recording([InstructionDraft('时间等待',{'类型':'时间等待','时长':0,'单位':'秒'})])
    def book(path,repeat,hide,unconnected):
        w.db.set_setting_values({'运行重复次数':str(repeat),'执行中隐藏主窗口':str(hide),'运行未连接模块':str(unconnected)})
        b=openpyxl.Workbook();repo.export_to_workbook(b,w.db);b.save(path);b.close()
    a,b=folder/'A.xlsx',folder/'B.xlsx'
    book(a,3,False,True);book(b,-1,True,False)
    w.data_import(str(a))
    assert w.spinBox.value()==3 and w.radioButton_2.isChecked()
    assert not is_modified(w)
    with patch('anclicker.app.Start_Win.QMessageBox.question',side_effect=AssertionError('unchanged project must not prompt')):
        w.open_project_path(str(b))
    assert w.radioButton.isChecked() and w.checkBox_2.isChecked() and not w.run_unconnected_checkbox.isChecked()
    assert not is_modified(w)
    w.radioButton_2.setChecked(True);w.spinBox.setValue(8)
    assert is_modified(w)
    with patch('anclicker.app.Start_Win.QMessageBox.question',return_value=QMessageBox.Cancel) as q:
        w.open_project_path(str(a));assert q.call_count==1
    assert w.spinBox.value()==8 and w.db.get_setting_value('当前文件路径')==str(b)
    with patch('anclicker.app.Start_Win.QMessageBox.question',return_value=QMessageBox.Discard):
        w.open_project_path(str(a))
    assert w.spinBox.value()==3 and not w.checkBox_2.isChecked()
    with patch('anclicker.app.Start_Win.QMessageBox.question',side_effect=AssertionError('unchanged project must not prompt')):
        w.open_project_path(str(b))
    assert w.spinBox.value()==8 and w.radioButton_2.isChecked() and w.checkBox_2.isChecked()
    assert w.db.get_setting_value('运行重复次数')=='8'
    clone=Host(folder/'db.sqlite')
    assert clone.spinBox.value()==8 and clone.checkBox_2.isChecked()
    assert not is_modified(clone)
    clone.db.set_setting_value('界面主题','dark')
    assert not is_modified(clone)
    repo.append_recording([InstructionDraft('时间等待',{'类型':'时间等待','时长':1,'单位':'秒'})])
    assert is_modified(w)
    with patch('anclicker.app.Start_Win.QMessageBox.question',return_value=QMessageBox.Save) as q:
        w.open_project_path(str(a));assert q.call_count==1
    saved=openpyxl.load_workbook(b)
    assert saved['命令'].max_row==3
    assert CACHE_KEY not in {r[1] for r in saved['设置'].iter_rows(min_row=2,values_only=True)}
    saved.close()
    assert not is_modified(w)
    before=w.project_run_controls.values()
    broken=folder/'bad.xlsx';broken.write_bytes(b'bad')
    with patch('anclicker.app.Start_Win.QMessageBox.warning'):
        w.open_project_path(str(broken))
    assert w.project_run_controls.values()==before and not is_modified(w)
    # Same-path selection reads external edits without a save prompt if local content is unchanged.
    f=openpyxl.load_workbook(a);f['命令']['F2']='external note';f.save(a);f.close()
    with patch('anclicker.app.Start_Win.QMessageBox.question',side_effect=AssertionError('unchanged reload must not prompt')):
        w.open_project_path(str(a))
    assert repo.list_commands()[0].note=='external note'
    print('PASS project controls, startup restore, clean switching, changed/save/discard/cancel, failed import, same-path external reload, local-cache export isolation')
