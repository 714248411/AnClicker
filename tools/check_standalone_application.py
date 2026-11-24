"""Isolated standalone export and real no-window process smoke checks."""
import os,sys,tempfile,json,subprocess,sqlite3,hashlib
from pathlib import Path
sys.path.insert(0,str(Path(__file__).resolve().parents[1]))
from openpyxl import Workbook,load_workbook
from anclicker.storage.database import DatabaseOperation
from anclicker.storage.graph_repository import GraphRepository
from anclicker.domain.instructions import InstructionDraft
from anclicker.app.standalone_export import export_directory as export_application,control_keys
ROOT=Path(__file__).resolve().parents[1]
with tempfile.TemporaryDirectory(prefix='standalone-check-') as tmp:
 root=Path(tmp);source=root/'source';source.mkdir();(source/'images').mkdir()
 db=DatabaseOperation(str(source/'命令集.db'));repo=GraphRepository(db.db_path,data_folder=source)
 repo.add_command(InstructionDraft('时间等待',{'时长':0.05,'单位':'秒'}))
 book=Workbook();repo.export_to_workbook(book,db);project=source/'test.xlsx';book.save(project);book.close()
 before=hashlib.sha256(project.read_bytes()).hexdigest()
 runtime=root/'runtime';runtime.mkdir();(runtime/'AnClicker.exe').write_bytes(b'fixture-runtime')
 (runtime/'Data').mkdir();(runtime/'Data/private.txt').write_text('excluded')
 (runtime/'secret.txt').write_text('excluded')
 (runtime/'models/.dual-runtime').mkdir(parents=True)
 (runtime/'models/.dual-runtime/session.json').write_text('excluded')
 keys={'结束运行':['ctrl','shift','f9'],'结束运行2':[],'暂停和恢复':['ctrl','shift','f10'],'开始运行':['f8']}
 target=root/'app'
 export_application(project,target,keys,{'运行重复次数':'1'},source,runtime=runtime)
 assert not (target/'secret.txt').exists() and not (target/'Data/private.txt').exists()
 assert not (target/'models/.dual-runtime').exists()
 config=json.loads((target/'standalone-project.json').read_text(encoding='utf8'))
 assert set(config['keys'])=={'exit','pause'}
 assert hashlib.sha256(project.read_bytes()).hexdigest()==before
 try:export_application(project,target,keys,{},source,runtime=runtime)
 except FileExistsError:pass
 else:raise AssertionError('existing output overwritten')
 moved=root/'moved-app';target.rename(moved)
 env=dict(os.environ,PYTHONUTF8='1');env.pop('ANCLICKER_DATA_DIR',None)
 result=subprocess.run([sys.executable,'-B','-X','utf8',str(ROOT/'main.py'),'--standalone-project',str(moved/'standalone-project.json')],cwd=root,env=env,capture_output=True,text=True,timeout=30)
 assert result.returncode==0,(result.returncode,result.stdout,result.stderr)
 log=(moved/'Data/logs/standalone.log').read_text(encoding='utf8')
 assert '完成第1次循环' in log,log
 assert '开始运行' not in json.dumps(config['keys'])
 # Exercise actual host control without sending keyboard events to other apps.
 probe=root/'control_probe.py'
 probe.write_text("""import sys, json, ctypes
from pathlib import Path
sys.path.insert(0, sys.argv[2])
from anclicker.app.standalone_runner import main
from anclicker.platform.qt_compat.QtCore import QTimer
from anclicker.platform.qt_compat.QtWidgets import QApplication
from ctypes.wintypes import MSG
errors=[]
occupied=len(sys.argv)>3
if occupied:
 for ident,vk in enumerate((0x78,0x79),100):
  assert ctypes.windll.user32.RegisterHotKey(None,ident,6,vk)
def ready(host, hotkeys):
 def event(action):
  if occupied:
   from unittest.mock import patch
   vk={'exit':0x78,'pause':0x79}[action]
   with patch.object(ctypes.windll.user32,'GetAsyncKeyState',return_value=0):
    hotkeys.poll_shared()
   with patch.object(ctypes.windll.user32,'GetAsyncKeyState',side_effect=lambda k:0x8000 if k in (vk,0x10,0x11) else 0):
    hotkeys.poll_shared();hotkeys.poll_shared()
   return
  msg=MSG();msg.message=0x0312;msg.wParam=next(k for k,v in hotkeys.registered.items() if v==action)
  hotkeys.nativeEventFilter(b'windows_dispatcher_MSG',ctypes.addressof(msg))
 def paused():
  try:
   assert not any(w.isVisible() for w in QApplication.topLevelWidgets())
   event('pause');assert host.worker.is_paused
  except BaseException as e:errors.append(repr(e));event('exit')
 def resumed():
  try:event('pause');assert not host.worker.is_paused
  except BaseException as e:errors.append(repr(e));event('exit')
 QTimer.singleShot(60,paused);QTimer.singleShot(140,resumed);QTimer.singleShot(240,lambda:event('exit'))
 actions=[action for action,_ in hotkeys.shared.values()] if occupied else hotkeys.registered.values()
 assert set(actions)=={'exit','pause'}
result=main(sys.argv[1],on_ready=ready)
assert not errors,errors
print('PASS native shortcut dispatch: pause, resume, exit; no visible editor')
raise SystemExit(result)
""",encoding='utf8')
 book=load_workbook(moved/'Data/project.xlsx');book['命令'].cell(2,3).value=json.dumps({'时长':5,'单位':'秒'});book.save(moved/'Data/project.xlsx');book.close()
 result=subprocess.run([sys.executable,'-B',str(probe),str(moved/'standalone-project.json'),str(ROOT)],cwd=root,env=env,capture_output=True,text=True,timeout=15)
 assert result.returncode==0,(result.returncode,result.stdout,result.stderr)
 print(result.stdout.strip())
 result=subprocess.run([sys.executable,'-B',str(probe),str(moved/'standalone-project.json'),str(ROOT),'occupied'],cwd=root,env=env,capture_output=True,text=True,timeout=15)
 assert result.returncode==0,(result.returncode,result.stdout,result.stderr)
 print('PASS occupied shortcuts: start, pause, resume and stop')
 # A referenced image is copied and rebased, rather than retaining its source path.
 image=source/'reference.png';image.write_bytes(b'image-resource-fixture')
 repo.add_command(InstructionDraft('图像点击',{'图像路径':str(image)}))
 book=Workbook();repo.export_to_workbook(book,db);book.save(project);book.close()
 resource_app=root/'resources-app';export_application(project,resource_app,keys,{},source,runtime=runtime)
 from anclicker.storage.project_paths import resolve_parameters
 book=load_workbook(resource_app/'Data/project.xlsx');params=json.loads(book['命令'].cell(3,3).value);book.close()
 resolved=resolve_parameters(params,'图像点击',resource_app/'Data',base=resource_app/'Data')
 copied=Path(resolved['图像路径']);assert copied.is_relative_to(resource_app) and copied.read_bytes()==image.read_bytes(),resolved
 print('PASS referenced image copied and rebased inside standalone folder')
 for name in ('结束运行','暂停和恢复'):
  bad=dict(keys);bad[name]=[]
  try:control_keys(bad)
  except ValueError:pass
  else:raise AssertionError('Missing essential shortcut accepted')
 bad=dict(keys);bad['暂停和恢复']=bad['结束运行']
 try:control_keys(bad)
 except ValueError:pass
 else:raise AssertionError('Conflicting shortcuts accepted')
 missing=root/'missing-app'
 book=load_workbook(project);book['命令'].cell(3,3).value=json.dumps({'图像路径':str(root/'absent-image.png')});book.save(project);book.close()
 try:export_application(project,missing,keys,{},source,runtime=runtime)
 except ValueError:pass
 else:raise AssertionError('Missing input was accepted')
 assert not missing.exists()
 print('PASS missing resources/essential keys/conflicting shortcuts rejected without incomplete output')
 print('PASS project export, private-data exclusion, no overwrite, moved folder, real standalone execution and automatic exit')
