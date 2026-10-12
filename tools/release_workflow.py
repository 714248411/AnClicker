"""Run the existing two-phase release workflow with local SDK paths."""
import os,sys,subprocess
from pathlib import Path
root=Path(__file__).resolve().parents[1]
env=dict(os.environ)
sdk=root/'.runtime-tools/dotnet'
env['DOTNET_ROOT']=str(sdk)
env['DOTNET_CLI_TELEMETRY_OPTOUT']='1'
env['DOTNET_NOLOGO']='1'
env['PATH']=str(sdk)+os.pathsep+env.get('PATH','')
env['PYTHONPATH']=str(root/'.runtime-tools')
env['PYTHONUTF8']='1'
for key,value in list(env.items()):
    if key.lower().endswith('_proxy') and value.startswith('socks5h://'):
        env[key]='socks5://'+value[len('socks5h://'):]
action=sys.argv[1]
if action == 'publish' and len(sys.argv) > 2:
    sys.path.insert(0, str(root))
    from info import UPDATE_CONFIG
    from publishing_credentials import publishing_environment
    env = publishing_environment(sys.argv[2], env, UPDATE_CONFIG)
output=root/'release/win-1.5.1-20261012-responsive'
if action=='build':
    command=[sys.executable,str(root/'packaging/发布Velopack.py'),'build','--output',str(output)]
elif action=='upgrade':
    command=[sys.executable,str(root/'packaging/smoke_velopack.py')]
else:
    command=[sys.executable,str(root/'packaging/发布Velopack.py'),action,'--output',str(output)]
    if action=='publish':command.append('--yes')
with (root/'validation'/('release-'+action+'.log')).open('w',encoding='utf-8') as log:
    result=subprocess.run(command,cwd=root,env=env,stdout=log,stderr=subprocess.STDOUT)
print(action+' exit code: '+str(result.returncode),flush=True)
raise SystemExit(result.returncode)
