"""Sync verified release assets using standard GitHub/Git Credential Manager authentication."""
import os,sys,json,subprocess,hashlib
from pathlib import Path

import sys as _import_sys
from pathlib import Path as _ImportPath
if __package__ in (None, ""):
    _import_sys.path.insert(0, str(_ImportPath(__file__).resolve().parents[1]))
from anclicker._imports import DeferredImports as _DeferredImports

# Dependencies declared here retain their existing on-demand loading boundaries.
_module_imports = _DeferredImports(globals(), {
    'requests': ('import', 'requests', (), False),
})

ROOT=Path(__file__).resolve().parents[1]
sys.path.insert(0,str(ROOT/'.local/cache'))
requests = _module_imports.load('requests')
repo='714248411/AnClicker'
session=requests.Session()
session.headers.update({'Accept':'application/vnd.github+json','X-GitHub-Api-Version':'2022-11-28'})
token=os.environ.get('GH_TOKEN') or os.environ.get('GITHUB_TOKEN')
if not token:
 env=dict(os.environ,GCM_INTERACTIVE='never',GIT_TERMINAL_PROMPT='0')
 result=subprocess.run(['git','credential','fill'],input='protocol=https\nhost=github.com\n\n',text=True,capture_output=True,env=env,timeout=30)
 if result.returncode==0:
  values=dict(line.split('=',1) for line in result.stdout.splitlines() if '=' in line)
  token=values.get('password')
if not token:
 print('GitHub authentication unavailable: no standard CLI token or Git Credential Manager credential.')
 raise SystemExit(2)
session.headers['Authorization']='Bearer '+token
try:
 r=session.get('https://api.github.com/repos/'+repo,timeout=30)
 print('repository_status:',r.status_code)
 if r.status_code!=200:raise SystemExit(3)
 data=r.json();print(json.dumps({'repository':data['full_name'],'default_branch':data['default_branch'],'permissions':data.get('permissions',{})}))
 r=session.get('https://api.github.com/repos/'+repo+'/releases',timeout=30);r.raise_for_status()
 print(json.dumps([{'id':x['id'],'tag':x['tag_name'],'draft':x['draft'],'assets':[{'name':a['name'],'size':a['size']} for a in x['assets']]} for x in r.json()[:5]],ensure_ascii=False))
except requests.RequestException as e:
 print('GitHub request failed:',type(e).__name__)
 raise SystemExit(4)
