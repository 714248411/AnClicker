"""Single-EXE packaging and relocation test using a harmless native runtime probe."""
import os,sys,tempfile,subprocess,struct,hashlib,json,zipfile,io
from pathlib import Path
sys.path.insert(0,str(Path(__file__).resolve().parents[1]))
from openpyxl import Workbook
from anclicker.storage.database import DatabaseOperation
from anclicker.storage.graph_repository import GraphRepository
from anclicker.domain.instructions import InstructionDraft
from anclicker.app.standalone_export import export_application,_temporary_directory,_windows_path
ROOT=Path(__file__).resolve().parents[1]
keys={'结束运行':['ctrl','shift','f9'],'结束运行2':[],'暂停和恢复':['ctrl','shift','f10']}
with _temporary_directory(prefix='ac-single-exe-',dir=tempfile.gettempdir()) as temporary:
 root=Path(temporary);seed=root/'project';seed.mkdir()
 image=seed/'reference.png';image.write_bytes(b'included-image-fixture')
 db=DatabaseOperation(str(seed/'命令集.db'));repo=GraphRepository(db.db_path,data_folder=seed)
 repo.add_command(InstructionDraft('图像点击',{'图像路径':str(image)}))
 book=Workbook();repo.export_to_workbook(book,db);project=seed/'test.xlsx';book.save(project);book.close()
 runtime=root/'runtime';runtime.mkdir();(runtime/'Data').mkdir();(runtime/'Data/private.txt').write_text('private')
 probe=root/'probe.cs';probe.write_text('''using System;using System.IO;
class Probe {static int Main() {
 string root=AppDomain.CurrentDomain.BaseDirectory;
 if (!File.Exists(Path.Combine(root,"standalone-project.json"))) return 21;
 if (Path.GetFullPath(Environment.GetEnvironmentVariable("ANCLICKER_DATA_DIR")) != Path.Combine(root,"Data")) return 22;
 if (Environment.GetEnvironmentVariable("ANCLICKER_STANDALONE_EXE")==null) return 23;
 File.AppendAllText(Path.Combine(root,"Data","probe.txt"),"ran\\n");
 return 17;
}}''',encoding='utf8')
 csc=Path(os.environ.get('SystemRoot','C:/Windows'))/'Microsoft.NET/Framework64/v4.0.30319/csc.exe'
 subprocess.run([str(csc),'/nologo','/target:winexe','/out:'+str(runtime/'AnClicker.exe'),str(probe)],check=True,capture_output=True)
 (runtime/'resources').mkdir();(runtime/'resources/runtime.txt').write_text('runtime-library-fixture')
 deep=Path('resources')/('d'*70)/('e'*70)/'long-path.txt'
 (runtime/deep).parent.mkdir(parents=True);(runtime/deep).write_text('long-path-fixture')
 output=root/'delivery';output.mkdir();target=output/'任务.exe'
 export_application(project,target,keys,{'运行重复次数':'1'},seed,runtime=runtime)
 assert list(output.iterdir())==[target]
 raw=target.read_bytes()
 magic,offset,length,sha=struct.unpack('<16sQQ32s',raw[-64:])
 assert magic==b'ANCLICKERAPP0001' and offset+length==len(raw)-64
 assert hashlib.sha256(raw[offset:offset+length]).digest()==sha
 with zipfile.ZipFile(io.BytesIO(raw[offset:offset+length])) as z:
  assert z.testzip() is None
  assert z.read(deep.as_posix())==b'long-path-fixture'
  assert z.read('resources/runtime.txt')==b'runtime-library-fixture'
  assert 'Data/private.txt' not in z.namelist()
  assert any(z.read(n)==b'included-image-fixture' for n in z.namelist() if n.endswith('.png'))
  config=json.loads(z.read('standalone-project.json'))
  assert set(config['keys'])=={'pause','exit'}
 before=target.read_bytes()
 try:export_application(project,target,keys,{},seed,runtime=runtime)
 except FileExistsError:pass
 else:raise AssertionError('overwrote existing EXE')
 assert target.read_bytes()==before
 moved=root/'moved';moved.mkdir();target.rename(moved/'改名后的任务.exe');target=moved/'改名后的任务.exe'
 seed.rename(root/'source-unavailable');runtime.rename(root/'runtime-unavailable')
 local=root/'user-cache';local.mkdir()
 env=dict(os.environ,LOCALAPPDATA=str(local),PATH=os.environ.get('SystemRoot','C:/Windows')+'/System32')
 env.pop('PYTHONPATH',None);env.pop('PYTHONHOME',None)
 for _ in range(2):
  result=subprocess.run([str(target)],cwd=moved,env=env,timeout=30)
  assert result.returncode==17,result.returncode
 cache=local/'AnClicker/StandaloneApps'/sha.hex()
 assert (cache/'Data/probe.txt').read_text()=='ran\nran\n'
 assert list(moved.iterdir())==[target]
 assert len(str(cache/deep))>260 and Path(_windows_path(cache/deep)).read_text()=='long-path-fixture'
 damaged=root/'damaged.exe';content=bytearray(target.read_bytes());content[-1]^=1;damaged.write_bytes(content)
 failed=subprocess.run([str(damaged)],cwd=moved,env=dict(env,ANCLICKER_STANDALONE_NO_ERROR_DIALOG='1'),timeout=30)
 assert failed.returncode==1
 assert '校验失败' in (local/'AnClicker-standalone-error.log').read_text(encoding='utf8')
 print('PASS paths beyond 260 characters; corrupted payload rejected before execution')
 print('PASS one EXE only; embedded image/runtime; rename/move; no original project/runtime/Python; persistent private cache; child exit code; no overwrite')
