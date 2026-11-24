"""Verify copied Data against the frozen app, including startup bootstrap."""
import contextlib,json,os,sqlite3,subprocess,sys,tempfile,uuid
from pathlib import Path
ROOT=Path(__file__).resolve().parents[1];sys.path.insert(0,str(ROOT))
from anclicker.storage.database import DatabaseOperation
import openpyxl
exe=ROOT/'artifacts/dist/v1.8.4/AnClicker/AnClicker.exe'
results=[]
for nested in (False,True):
 with tempfile.TemporaryDirectory(prefix='ac-copy-data-') as td:
  outer=Path(td)/'Data';data=outer/'Data' if nested else outer
  data.mkdir(parents=True);(data/'exports').mkdir()
  db=DatabaseOperation(str(data/'命令集.db'))
  project=data/'exports/迁移测试.xlsx'
  book=openpyxl.Workbook();db.export_instruction_workbook(book);book.save(project);book.close()
  old='Z:/old/Data/exports/迁移测试.xlsx'
  db.set_setting_value('当前文件路径',old)
  db.writes_to_recently_opened_files(old)
  db.set_setting_value('定时运行任务',json.dumps([{'id':'copy-test','path':old,'enabled':False,'repeat':'每天','next_run':'2026-11-02T12:00:00'}]))
  env=dict(os.environ,ANCLICKER_DATA_DIR=str(outer),ANCLICKER_SINGLETON_KEY=uuid.uuid4().hex,ANCLICKER_SMOKE_LIGHTWEIGHT='1',PYTHONDONTWRITEBYTECODE='1')
  subprocess.run([str(exe),'--release-smoke'],cwd=td,env=env,check=True,timeout=90,capture_output=True)
  assert json.loads((data/'startup-ready.json').read_text())['ready']
  with contextlib.closing(sqlite3.connect(data/'命令集.db')) as conn:
   settings=dict(conn.execute('SELECT 设置项,值 FROM 设置'))
   assert Path(settings['当前文件路径'])==project,settings['当前文件路径']
   assert any(Path(p)==project for p, in conn.execute('SELECT 文件路径 FROM 最近打开'))
   assert Path(json.loads(settings['定时运行任务'])[0]['path'])==project
  assert list((data/'migration_backups').glob('*.db'))
  results.append({'nested':nested,'passed':True})
  print('PASS frozen copied Data nested='+str(nested),flush=True)
(ROOT/'artifacts/validation/v1.8.4/frozen-data-migration.json').write_text(json.dumps(results))
