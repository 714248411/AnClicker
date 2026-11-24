"""Two real source versions; transfer Data only, then make old paths unavailable."""
import json,os,shutil,subprocess,sys,tempfile,zipfile
from pathlib import Path
ROOT=Path(__file__).resolve().parents[1]
base=Path(tempfile.mkdtemp(prefix='data-two-versions-',dir=ROOT/'artifacts/validation'))
old=base/'old';new=base/'new';old.mkdir();new.mkdir()
with zipfile.ZipFile(ROOT/'artifacts/release/v1.7.8/public/AnClicker-v1.7.8-win-DaiMa.zip') as archive:
 for item in archive.infolist():
  relative=Path(*Path(item.filename).parts[1:])
  if item.is_dir() or not relative.parts:continue
  assert not relative.is_absolute() and '..' not in relative.parts
  target=old/relative;target.parent.mkdir(parents=True,exist_ok=True);target.write_bytes(archive.read(item))
# Give the new version its own source tree too: no fallback to the working repo's Data.
for path in old.rglob('*'):
 if path.is_file():
  target=new/path.relative_to(old);target.parent.mkdir(parents=True,exist_ok=True);shutil.copy2(path,target)
for folder in ('anclicker','tools','models'):
 for path in (ROOT/folder).rglob('*.py'):
  if '__pycache__' in path.parts:continue
  target=new/path.relative_to(ROOT);target.parent.mkdir(parents=True,exist_ok=True);shutil.copy2(path,target)
for name in ('info.py','main.py'):
 shutil.copy2(ROOT/name,new/name)
def run(code,cwd,data):
 env=dict(os.environ,ANCLICKER_DATA_DIR=str(data),PYTHONPATH=str(cwd),PYTHONDONTWRITEBYTECODE='1',QT_QPA_PLATFORM='offscreen')
 result=subprocess.run([sys.executable,'-B','-X','utf8','-c',code],cwd=cwd,env=env,capture_output=True,text=True,encoding='utf8',timeout=90)
 assert result.returncode==0,result.stdout+result.stderr
 print(result.stdout,flush=True)
 return result.stdout
create=r'''
from pathlib import Path
import json,os
import openpyxl
from anclicker.app.paths import ensure_data_directories,DATA_FOLDER
from anclicker.storage.database import DatabaseOperation
from anclicker.domain.instructions import InstructionDraft
ensure_data_directories();data=Path(DATA_FOLDER);db=DatabaseOperation();repo=db.get_graph_repository()
image=data/'images'/'nested'/'migration.png';image.parent.mkdir(parents=True);image.write_bytes(b'portable-image')
external=data/'files'/'input.txt';external.parent.mkdir();external.write_text('portable-file')
workbook=data/'files'/'input.xlsx';b=openpyxl.Workbook();b.save(workbook);b.close()
drafts=[InstructionDraft('时间等待',{'类型':'时间等待','时长':0,'单位':'秒'},note='order-'+str(i)) for i in range(139)]
drafts += [InstructionDraft('图像点击',{'图像路径':str(image),'精度':0.8}),InstructionDraft('获取Excel',{'工作簿':str(workbook)}),InstructionDraft('运行外部文件',{'文件路径':str(external)})]
repo.append_recording(drafts)
# Preserve historical absolute references for relocation verification.
import sqlite3
with sqlite3.connect(db.db_path) as conn:
 for command in repo.list_commands()[-3:]:
  fields={'图像点击':('图像路径',image),'获取Excel':('工作簿',workbook),'运行外部文件':('文件路径',external)}
  key,path=fields[command.type_id];params=dict(command.parameters);params[key]=str(path)
  conn.execute('UPDATE 命令 SET 参数JSON=? WHERE ID=?',(json.dumps(params,ensure_ascii=False),command.id))
project=data/'exports'/'142条.xlsx';b=openpyxl.Workbook();repo.export_to_workbook(b,db);b.save(project);b.close()
db.set_setting_value('当前文件路径',str(project));db.writes_to_recently_opened_files(str(project))
with sqlite3.connect(db.db_path) as conn:
 (data/'expected-graph.json').write_text(json.dumps({table:conn.execute('SELECT * FROM "'+table+'" ORDER BY 1').fetchall() for table in ('节点','节点连接')},ensure_ascii=False),encoding='utf8')
(data/'expected.json').write_text(json.dumps([{'id':c.id,'type':c.type_id,'parameters':c.parameters,'note':c.note} for c in repo.list_commands()],ensure_ascii=False),encoding='utf8')
print('Created 142 commands with historical v1.7.8 source')
'''
run(create,old,old/'Data')
shutil.copytree(old/'Data',new/'Data')
old.rename(base/'old-offline')
verify=r'''
import json,os
from pathlib import Path
import openpyxl
from anclicker.app.startup_environment import prepare_environment
prepare_environment()
from anclicker.storage.database import DatabaseOperation
from anclicker.app.paths import DATA_FOLDER
from anclicker.storage.portable_migration import relocate_command_files
from anclicker.storage.legacy_workbook import is_current_workbook
from anclicker.storage.migration_tool import needs_batch_migration
root=Path(DATA_FOLDER);db=DatabaseOperation();repo=db.get_graph_repository();expected=json.loads((root/'expected.json').read_text(encoding='utf8'))
project=Path(db.get_setting_value('当前文件路径'));assert project.is_relative_to(root) and project.is_file()
def check():
 commands=repo.list_commands();assert len(commands)==142
 for command,saved in zip(commands,expected):
  assert command.id==saved['id'] and command.type_id==saved['type'] and command.note==saved['note']
  assert command.parameters==relocate_command_files(saved['parameters'],root),(command.id,command.parameters)
 for command in commands[-3:]:
  key={'图像点击':'图像路径','获取Excel':'工作簿','运行外部文件':'文件路径'}[command.type_id]
  path=Path(command.parameters[key]);path=path if path.is_absolute() else root/path
  assert path.is_file() and path.resolve().is_relative_to(root.resolve()),path
# Copied Data preserves command paths until the user accepts adaptation.
from anclicker.platform.qt_compat.QtWidgets import QApplication,QMessageBox
from tools.check_xlsm_drop import DropHost
from unittest.mock import patch
from anclicker.storage.data_partitions import ensure_runtime_paths
app=QApplication.instance() or QApplication([]);host=DropHost(Path(db.db_path))
host.workspace.reload_graph=lambda *args,**kw:None
from types import SimpleNamespace
host.view_workspace=SimpleNamespace(refresh_all=lambda:None)
with patch.object(QMessageBox,'question',return_value=QMessageBox.Yes):
 assert ensure_runtime_paths(host)
check()
book=openpyxl.load_workbook(project);assert is_current_workbook(book) and not needs_batch_migration(book)
book.close()
from anclicker.platform.qt_compat.QtWidgets import QApplication,QMessageBox
from tools.check_xlsm_drop import DropHost
from unittest.mock import patch
app=QApplication.instance() or QApplication([]);host=DropHost(Path(db.db_path))
host.workspace.reload_graph=lambda *args,**kw:None
def fail(*args,**kw):raise AssertionError('Unexpected migration/error dialog: '+str(args))
with patch.object(QMessageBox,'question',return_value=QMessageBox.Yes),patch.object(QMessageBox,'warning',side_effect=fail),patch.object(QMessageBox,'information',side_effect=fail):
 host.data_import(str(project))
assert Path(db.get_setting_value('当前文件路径'))==project
# Image imports may store Data-relative paths; compare their resolved file bytes.
commands=repo.list_commands();assert len(commands)==142
for c,s in zip(commands,expected):
 assert (c.id,c.type_id,c.note)==(s['id'],s['type'],s['note'])
 before=dict(s['parameters']);after=dict(c.parameters)
 for key in ('图像路径','工作簿','文件路径'):
  before.pop(key,None);after.pop(key,None)
 assert before==after
import sqlite3
with sqlite3.connect(db.db_path) as conn:
 graph={table:[list(row) for row in conn.execute('SELECT * FROM "'+table+'" ORDER BY 1')] for table in ('节点','节点连接')}
assert graph==json.loads((root/'expected-graph.json').read_text(encoding='utf8'))
for c in commands[-3:]:
 key={'图像点击':'图像路径','获取Excel':'工作簿','运行外部文件':'文件路径'}[c.type_id];p=Path(c.parameters[key]);p=p if p.is_absolute() else root/p
 assert p.is_file() and p.resolve().is_relative_to(root.resolve())
print('PASS 142 commands retained, graph format recognized, images/workbooks/files all inside new Data')
'''
run(verify,new,new/'Data')
# Fresh process proves the repaired references survive restart.
run(verify.replace('check()\nbook=', '# Import round-trip may store relative image references.\nbook='),new,new/'Data')
report={'passed':True,'old_version':'1.7.8','new_version':'working source after 1.8.4','commands':142,'old_directory_unavailable':True,'data_only_copy':True,'restart':True,'directory':str(base)}
(base/'result.json').write_text(json.dumps(report,ensure_ascii=False,indent=2),encoding='utf8')
print(json.dumps(report,ensure_ascii=False))
