"""Check that publishing credentials are absent from source and release content."""
import sys, zipfile, os
from pathlib import Path

import sys as _import_sys
from pathlib import Path as _ImportPath
if __package__ in (None, ""):
    _import_sys.path.insert(0, str(_ImportPath(__file__).resolve().parents[1]))
from anclicker._imports import DeferredImports as _DeferredImports

# Dependencies declared here retain their existing on-demand loading boundaries.
_module_imports = _DeferredImports(globals(), {
    'UPDATE_CONFIG': ('from', 'info', ('UPDATE_CONFIG',), 0),
    'publishing_environment': ('from', 'tools.packaging.publishing_credentials', ('publishing_environment',), 0),
})

ROOT=Path(__file__).resolve().parents[1]
sys.path.insert(0,str(ROOT))
UPDATE_CONFIG = _module_imports.load('UPDATE_CONFIG')
publishing_environment = _module_imports.load('publishing_environment')
values=publishing_environment(sys.argv[1], {}, UPDATE_CONFIG)
secrets=[values[UPDATE_CONFIG[k+'_env']].encode() for k in ('access_key','secret_key')]
skip={'.local','artifacts','.venv','.venv-build','.local/toolchains/python-3.10.11','.local/cache','node_modules','runtime','build','dist','release','.git','__pycache__'}
count=0
for folder, dirs, files in os.walk(ROOT):
    dirs[:] = [name for name in dirs if name not in skip and name != 'data']
    for name in files:
        path=Path(folder)/name
        if path.suffix.lower() not in {'.py','.js','.json','.txt','.log','.md','.toml','.yml','.yaml','.ini','.spec','.ui'}:continue
        content=path.read_bytes()
        if any(secret in content for secret in secrets): raise SystemExit('Credential found in workspace file; publishing blocked')
        count+=1
package=Path(sys.argv[2])
with zipfile.ZipFile(package) as archive:
    for member in archive.infolist():
        if member.is_dir():continue
        content=archive.read(member)
        if any(secret in content for secret in secrets):raise SystemExit('Credential found in release; publishing blocked')
print('Credential privacy check passed; source files:',count)
