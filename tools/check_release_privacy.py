"""Check that publishing credentials are absent from source and release content."""
import sys, zipfile, os
from pathlib import Path
ROOT=Path(__file__).resolve().parents[1]
sys.path.insert(0,str(ROOT))
from info import UPDATE_CONFIG
from publishing_credentials import publishing_environment
values=publishing_environment(sys.argv[1], {}, UPDATE_CONFIG)
secrets=[values[UPDATE_CONFIG[k+'_env']].encode() for k in ('access_key','secret_key')]
skip={'.venv','.venv-build','.build-python','.runtime-tools','node_modules','runtime','build','dist','release','.git','__pycache__'}
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
