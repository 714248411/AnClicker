import sys,json
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

root=Path(__file__).resolve().parents[1];sys.path.insert(0,str(root/'.local/cache'))
requests = _module_imports.load('requests')
try:
    r=requests.get('https://updates.ytsoftware.cn/an-clicker/win-x64/releases.win-x64.json',timeout=(15,45));r.raise_for_status()
    feed=r.json();(root/'artifacts/validation/remote-feed.json').write_text(json.dumps(feed),encoding='utf-8')
    print('Public versions:',sorted({a['Version'] for a in feed['Assets']}))
except Exception as e:
    print(type(e).__name__+': '+str(e));raise SystemExit(1)
