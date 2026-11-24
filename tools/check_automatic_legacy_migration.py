"""Automatic legacy import must complete without modal migration prompts."""
import os,sys,tempfile,json
from pathlib import Path
from unittest.mock import patch
sys.path.insert(0,str(Path(__file__).resolve().parents[1]))
with tempfile.TemporaryDirectory() as td:
 os.environ['ANCLICKER_DATA_DIR']=str(Path(td)/'Data')
 from tools.check_project_controls import Host
 from openpyxl import Workbook
 from anclicker.storage.legacy_workbook import LEGACY_HEADERS
 from anclicker.ui.project_changes import is_modified
 from anclicker.app.Start_Win import QMessageBox
 folder=Path(td);w=Host(folder/'db.sqlite')
 source=folder/'old.xlsx';b=Workbook();b.remove(b.active)
 for index,name in enumerate(('第一分支','第二分支'),1):
  sheet=b.create_sheet(name);sheet.append(LEGACY_HEADERS)
  sheet.append([index,name,'文本输入',"{'手动输入': 'False'}",None,None,None,1,'自动跳过',''])
 settings=b.create_sheet('设置');settings.append(['[Config]',None]);settings.append(['当前分支','第二分支'])
 b.save(source);original=source.read_bytes();w.db.writes_to_recently_opened_files(str(source))
 def no_dialog(*args,**kw):raise AssertionError('Unexpected modal: '+str(args))
 with patch.object(QMessageBox,'question',side_effect=no_dialog),patch.object(QMessageBox,'information',side_effect=no_dialog),patch.object(QMessageBox,'warning',side_effect=no_dialog):
  w.data_import(str(source))
  target=Path(w.db.get_setting_value('当前文件路径'))
  assert target!=source and target.is_file()
  assert w.workspace.repository.list_commands()[0].parameters['内容']=='第二分支'
  assert not is_modified(w)
  recent=w.db.get_recently_opened_file('文件列表')
  assert str(source) not in recent and len(recent)==2,recent
  assert (target.parent/'原始备份.xlsx').read_bytes()==original
  assert list(target.parent.glob('导入前指令备份*.xlsx'))
  w.data_import(str(target));assert not is_modified(w)
 assert source.read_bytes()==original
 # Unknown content must not become a partially migrated "successful" project.
 before=w.workspace.repository.list_commands();b['第一分支'].cell(2,3).value='未知旧指令';b.save(source)
 with patch.object(QMessageBox,'warning') as warning:
  w.data_import(str(source));assert warning.called
 assert Path(w.db.get_setting_value('当前文件路径'))==target
 assert w.workspace.repository.list_commands()==before
 b.close()
 print('PASS automatic migration: no confirmation dialogs, original active branch, all branches recent, backups, repeat open, atomic failure')
