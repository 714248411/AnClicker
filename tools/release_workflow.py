"""Run the existing two-phase release workflow with local SDK paths."""
import os,sys,subprocess
from pathlib import Path

import sys as _import_sys
from pathlib import Path as _ImportPath
if __package__ in (None, ""):
    _import_sys.path.insert(0, str(_ImportPath(__file__).resolve().parents[1]))
from anclicker._imports import DeferredImports as _DeferredImports

# Dependencies declared here retain their existing on-demand loading boundaries.
_module_imports = _DeferredImports(globals(), {
    'anclicker': ('import', 'anclicker', (), False),
    'UPDATE_CONFIG': ('from', 'info', ('UPDATE_CONFIG',), 0),
    'publishing_environment': ('from', 'tools.packaging.publishing_credentials', ('publishing_environment',), 0),
    'VERSION': ('from', 'info', ('VERSION',), 0),
})

root=Path(__file__).resolve().parents[1]
sys.path.insert(0, str(root))
anclicker = _module_imports.load('anclicker')
env=dict(os.environ)
sdk=root/'.local/cache/dotnet'
env['DOTNET_ROOT']=str(sdk)
env['DOTNET_CLI_TELEMETRY_OPTOUT']='1'
env['DOTNET_NOLOGO']='1'
env['PATH']=str(sdk)+os.pathsep+env.get('PATH','')
env['PYTHONPATH']=str(root/'.local/cache')
env['PYTHONUTF8']='1'
for key,value in list(env.items()):
    if key.lower().endswith('_proxy') and value.startswith('socks5h://'):
        env[key]='socks5://'+value[len('socks5h://'):]
action=sys.argv[1]
if action == 'publish' and len(sys.argv) > 2:
    sys.path.insert(0, str(root))
    UPDATE_CONFIG = _module_imports.load('UPDATE_CONFIG')
    publishing_environment = _module_imports.load('publishing_environment')
    env = publishing_environment(sys.argv[2], env, UPDATE_CONFIG)
VERSION = _module_imports.load('VERSION')
output=root/('artifacts/release/win-'+VERSION+'-20261013-verified')
if action=='build':
    command=[sys.executable,str(root/'tools/packaging/发布Velopack.py'),'build','--output',str(output)]
elif action=='upgrade':
    command=[sys.executable,str(root/'tools/packaging/smoke_velopack.py')]
else:
    command=[sys.executable,str(root/'tools/packaging/发布Velopack.py'),action,'--output',str(output)]
    if action=='publish':command.append('--yes')
with (root/'artifacts/validation'/('release-'+action+'.log')).open('w',encoding='utf-8') as log:
    result=subprocess.run(command,cwd=root,env=env,stdout=log,stderr=subprocess.STDOUT)
print(action+' exit code: '+str(result.returncode),flush=True)
raise SystemExit(result.returncode)
