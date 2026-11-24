"""Release the complete 1.8.4 app through the verified Qiniu workflow."""
import os,sys,subprocess,json
from pathlib import Path
ROOT=Path(__file__).resolve().parents[1];sys.path.insert(0,str(ROOT))
from info import UPDATE_CONFIG,VERSION,APP_ID,EXECUTABLE_NAME
assert VERSION=='1.8.4'
APP=ROOT/'artifacts/dist/v1.8.4/AnClicker'
OUT=ROOT/'artifacts/release/v1.8.4-qiniu'
SDK=ROOT/'.local/cache/dotnet'
env=dict(os.environ,DOTNET_ROOT=str(SDK),DOTNET_CLI_TELEMETRY_OPTOUT='1',DOTNET_NOLOGO='1',PYTHONUTF8='1',PYTHONDONTWRITEBYTECODE='1')
env['PATH']=str(SDK)+os.pathsep+env.get('PATH','')
for key,value in {'ProgramFiles':'C:/Program Files','ProgramFiles(x86)':'C:/Program Files (x86)','ProgramData':'C:/ProgramData','APPDATA':'C:/Users/Administrator/AppData/Roaming','LOCALAPPDATA':'C:/Users/Administrator/AppData/Local','USERPROFILE':'C:/Users/Administrator','SystemRoot':'C:/Windows'}.items():env.setdefault(key,value)
os.environ.update(env)
def run(args):subprocess.run(args,cwd=ROOT,env=env,check=True)
action=sys.argv[1]
if action=='restore':run([str(SDK/'dotnet.exe'),'tool','restore'])
elif action=='help':run([str(SDK/'dotnet.exe'),'tool','run','vpk','--','pack','--help'])
elif action=='pack':
 assert not OUT.exists(),'Use a new output directory'
 # Startup probes may create an empty image folder; user Data belongs at portable root.
 if (APP/'Data').exists():
  assert not any((APP/'Data').iterdir()), 'Never package application user data'
  (APP/'Data').rmdir()
 run([str(SDK/'dotnet.exe'),'tool','run','vpk','pack','--packId',APP_ID,'--packVersion',VERSION,'--packDir',str(APP),'--mainExe',EXECUTABLE_NAME,'--channel',UPDATE_CONFIG['runtime'],'--runtime',UPDATE_CONFIG['runtime'],'--packTitle','AnClicker','--noInst','--icon',str(ROOT/'resources/clicker.ico'),'--releaseNotes',str(ROOT/'tools/packaging/RELEASE_NOTES.md'),'--outputDir',str(OUT)])
elif action=='startup':
 sys.path.insert(0,str(ROOT/'tools/packaging'))
 from tools.packaging.发布门槛 import ReleaseContext,validate_release
 validate_release(ReleaseContext(ROOT,APP,OUT,OUT/UPDATE_CONFIG['portable_name'],APP_ID,APP_ID,VERSION,UPDATE_CONFIG['runtime']))
elif action=='validate':
 sys.path.insert(0,str(ROOT/'tools/packaging'))
 from tools.packaging.发布Velopack import validate_local,PublishConfig
 validate_local(PublishConfig.from_environment(),OUT,APP)
elif action=='upgrade':run([sys.executable,'tools/packaging/smoke_velopack.py','--app',str(APP)])
elif action=='publish':
 from tools.publishing_credentials import publishing_environment
 env=publishing_environment(sys.argv[2],env,UPDATE_CONFIG)
 run([sys.executable,'tools/packaging/发布Velopack.py','publish','--output',str(OUT),'--app-dir',str(APP),'--yes'])
else:raise ValueError('unknown action')
