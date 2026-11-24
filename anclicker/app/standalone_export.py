"""Export one saved project with a self-contained Windows runtime."""
from contextlib import closing,contextmanager
import json, os, shutil, sqlite3, subprocess, sys, tempfile, uuid, zipfile
from pathlib import Path

MANIFEST = 'standalone-project.json'
RUNTIME_DIRS = frozenset('anclicker certifi charset_normalizer cv2 defaults integrations legacy models numpy numpy.libs ocr_models onnxruntime PIL psutil pyclipper pyreadline3-3.5.6.dist-info PySide2 Pythonwin pywin32_system32 rapidocr_onnxruntime resources runtime setuptools shapely Shapely.libs shiboken2 tcl8 tokenizers velopack win32 yaml _tcl_data _tk_data'.split())


def _windows_path(path):
 value=os.path.abspath(os.fspath(path))
 if os.name!='nt' or value.startswith('\\\\?\\'):return value
 return '\\\\?\\UNC\\'+value[2:] if value.startswith('\\\\') else '\\\\?\\'+value

@contextmanager
def _temporary_directory(prefix,dir):
 parent=Path(dir).resolve()
 folder=Path(tempfile.mkdtemp(prefix=prefix,dir=parent)).resolve()
 try:yield str(folder)
 finally:
  if folder.parent!=parent or not folder.name.startswith(prefix):
   raise RuntimeError('临时打包目录超出预期位置，停止清理。')
  if folder.exists():shutil.rmtree(_windows_path(folder))

def control_keys(shortcuts):
 from anclicker.platform.services import normalize_hotkey
 result = {'exit': [], 'pause': list(normalize_hotkey(shortcuts.get('暂停和恢复', [])))}
 for name in ('结束运行', '结束运行2'):
  keys = list(normalize_hotkey(shortcuts.get(name, [])))
  if keys and keys not in result['exit']:result['exit'].append(keys)
 if not result['exit'] or not result['pause']:raise ValueError('请先在设置中配置结束运行和暂停/恢复快捷键。')
 if result['pause'] in result['exit']:raise ValueError('暂停/恢复快捷键不能与退出快捷键相同。')
 return result

def prepare_project(project, destination, controls, resource_root):
 from openpyxl import load_workbook, Workbook
 from anclicker.storage.database import DatabaseOperation
 from anclicker.storage.graph_repository import GraphRepository
 from anclicker.storage.project_paths import resolve_parameters
 from anclicker.storage.data_bundle import export_data
 project=Path(project).resolve();destination=Path(destination)
 with tempfile.TemporaryDirectory(prefix='ac-project-export-') as temporary:
  seed=Path(temporary)/'seed';seed.mkdir();db=DatabaseOperation(str(seed/'命令集.db'));repo=GraphRepository(db.db_path,data_folder=seed)
  book=load_workbook(project)
  try:repo.import_from_workbook(book,source_path=str(project),preserve_paths=True)
  finally:book.close()
  with closing(sqlite3.connect(db.db_path)) as conn, conn:
   for cid,kind,raw in conn.execute('SELECT ID,类型标识,参数JSON FROM 命令').fetchall():
    params=resolve_parameters(json.loads(raw),kind,resource_root,base=project.parent)
    conn.execute('UPDATE 命令 SET 参数JSON=? WHERE ID=?',(json.dumps(params,ensure_ascii=False),cid))
   for folder, in conn.execute('SELECT 路径 FROM 资源文件夹').fetchall():
    if not Path(folder).is_absolute():
     resolved=Path(resource_root)/folder
     if folder=='images' and not resolved.exists():resolved=seed/'images';resolved.mkdir(exist_ok=True)
     conn.execute('UPDATE OR IGNORE 资源文件夹 SET 路径=? WHERE 路径=?',(str(resolved),folder))
  for key,value in controls.items():db.set_setting_value(key,str(value))
  db.set_setting_value('当前文件路径',str(seed/'project.xlsx'))
  normalized=Workbook();repo.export_to_workbook(normalized,db);normalized.save(seed/'project.xlsx');normalized.close()
  archive=Path(temporary)/'project.zip'
  export_data(seed,archive,project_only=True,resource_root=resource_root)
  with zipfile.ZipFile(archive) as z:z.extractall(destination)
 return destination/'Data'/'project.xlsx'

def runtime_directory(progress, *, include_crawl=True):
 if getattr(sys,'frozen',False):return Path(sys.executable).parent
 root=Path(__file__).resolve().parents[2]
 # Build the current sources, never reuse an older release's executable.
 build=root/'artifacts'/'standalone-build'/uuid.uuid4().hex
 build.mkdir(parents=True)
 progress('源码模式：正在构建独立运行环境，首次构建耗时较长…')
 env=dict(os.environ,PYTHONDONTWRITEBYTECODE='1',PYTHONUTF8='1')
 with (build/'build.log').open('w',encoding='utf8') as log:
  result=subprocess.run([sys.executable,'-m','PyInstaller','--noconfirm','--distpath',str(build/'dist'),'--workpath',str(build/'work'),str(root/'tools/packaging/main.spec')],cwd=root,env=env,stdout=log,stderr=subprocess.STDOUT,creationflags=getattr(subprocess,'CREATE_NO_WINDOW',0))
 if result.returncode:raise RuntimeError('运行环境构建失败，日志：'+str(build/'build.log'))
 if include_crawl:
  from tools.packaging.crawl_runtime import stage as stage_crawl
  stage_crawl(root,build/'dist'/'AnClicker')
 return build/'dist'/'AnClicker'

def copy_runtime(source,destination,progress,profile=None):
 source=Path(_windows_path(source));destination=Path(_windows_path(destination))
 if not (source/'AnClicker.exe').is_file():raise ValueError('缺少可分发的 AnClicker.exe 运行环境。')
 for entry in source.iterdir():
  if entry.is_symlink():raise ValueError('运行环境不可包含链接。')
  if entry.is_dir() and entry.name in RUNTIME_DIRS:
   if profile and profile.get('mode')=='desktop' and entry.name in {'models','runtime'}:continue
   progress('复制运行库：'+entry.name)
   shutil.copytree(entry,destination/entry.name,ignore=shutil.ignore_patterns('__pycache__','*.log','.dual-runtime','.private','*.partial'))
  elif entry.is_file() and (entry.suffix.lower() in {'.dll','.pyd'} or entry.name in {'AnClicker.exe','base_library.zip','info.py','ai-build-manifest.json'}):shutil.copy2(entry,destination/entry.name)

def export_directory(project,target,shortcuts,controls,resource_root,progress=lambda _:None,*,runtime=None):
 project=Path(project).resolve();target=Path(target).resolve();keys=control_keys(shortcuts)
 if target.exists():raise FileExistsError('目标目录已存在，请使用新的应用目录。')
 if not project.is_file():raise FileNotFoundError('项目文件不存在。')
 target.parent.mkdir(parents=True,exist_ok=True)
 with _temporary_directory(prefix='.anclicker-app-',dir=target.parent) as temporary:
  staged=Path(temporary)/'app';staged.mkdir()
  progress('收集项目及引用资源…');prepare_project(project,staged,controls,Path(resource_root))
  from anclicker.app.standalone_dependencies import runtime_profile
  profile=runtime_profile(staged/'Data')
  source=Path(runtime) if runtime else runtime_directory(progress,include_crawl=profile['mode']!='desktop')
  if target.is_relative_to(source):raise ValueError('请保存到程序运行库目录之外。')
  progress('复制独立运行环境（'+('桌面精简' if profile['mode']=='desktop' else '完整兼容')+'）…');copy_runtime(source,staged,progress,profile)
  config={'format':1,'name':project.stem,'project':'Data/project.xlsx','keys':keys,'dependencies':profile}
  (staged/MANIFEST).write_text(json.dumps(config,ensure_ascii=False,indent=2),encoding='utf8')
  (staged/'使用说明.txt').write_text('双击 AnClicker.exe 即运行项目，无编辑界面。请保持整个文件夹完整。\n退出：'+' / '.join('+'.join(k) for k in keys['exit'])+'\n暂停/恢复：'+'+'.join(keys['pause'])+'\n任务完成后自动退出。快捷键取自打包时设置。\n日志位于 Data/logs/standalone.log。外部软件、账号与授权仍需目标电脑配置。\n',encoding='utf8')
  staged.rename(target)
 return target

def export_application(project,target,shortcuts,controls,resource_root,progress=lambda _:None,*,runtime=None):
 """Emit exactly one transferable EXE; runtime and project are embedded."""
 import hashlib,struct
 target=Path(target).resolve()
 if target.suffix.lower()!='.exe':raise ValueError('独立应用必须保存为 .exe 文件。')
 if target.exists():raise FileExistsError('目标文件已存在，请使用新的 EXE 文件名。')
 control_keys(shortcuts)
 if not Path(project).is_file():raise FileNotFoundError('项目文件不存在。')
 target.parent.mkdir(parents=True,exist_ok=True)
 if getattr(sys,'frozen',False):
  from anclicker.app.paths import resource_path
  launcher=resource_path('resources/standalone/launcher.exe')
  if not launcher.is_file():raise RuntimeError('当前程序缺少单文件启动器，请更新程序后重试。')
 else:
  from tools.packaging.single_exe_launcher import ensure_launcher
  launcher=ensure_launcher(Path(__file__).resolve().parents[2])
 with _temporary_directory(prefix='.anclicker-single-',dir=target.parent) as temporary:
  temporary=Path(temporary);staged=temporary/'app'
  export_directory(project,staged,shortcuts,controls,resource_root,progress,runtime=runtime)
  progress('将执行步骤、图片和运行库封装为单个 EXE…')
  archive_root=Path(_windows_path(staged))
  output=temporary/'application.exe'
  digest=hashlib.sha256()
  with output.open('xb') as result:
   with launcher.open('rb') as source:shutil.copyfileobj(source,result)
   offset=result.tell()
   # A write-only stream keeps ZIP offsets relative to the embedded payload.
   class PayloadWriter:
    def write(self, block):
     written = result.write(block)
     digest.update(block)
     return written

    def flush(self):
     result.flush()

   with zipfile.ZipFile(PayloadWriter(),'w',compression=zipfile.ZIP_DEFLATED,compresslevel=6,allowZip64=True) as archive:
    for path in sorted(archive_root.rglob('*')):
     if path.is_symlink():raise ValueError('独立应用不可包含符号链接。')
     if path.is_file():archive.write(path,path.relative_to(archive_root).as_posix())
   length=result.tell()-offset
   result.write(struct.pack('<16sQQ32s',b'ANCLICKERAPP0001',offset,length,digest.digest()))
  progress('检查单文件应用完整性…')
  with zipfile.ZipFile(output) as archive:
   bad=archive.testzip()
   if bad:raise RuntimeError('内置资源校验失败：'+bad)
  # Windows rename fails if another export created this name in the meantime.
  if target.exists():raise FileExistsError('目标文件已存在，请使用新的 EXE 文件名。')
  output.rename(target)
 return target
