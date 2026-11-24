from pathlib import Path
import zipfile
root=Path(__file__).resolve().parents[1];app=(root/'artifacts/dist/v1.8.3/AnClicker').resolve()
with zipfile.ZipFile(root/'artifacts/release/v1.8.3-qiniu/AnClicker-1.8.3-win-x64-full.nupkg') as z:
 expected={n[8:] for n in z.namelist() if n.startswith('lib/app/') and not n.endswith('/')}
extra=[p for p in app.rglob('*') if p.is_file() and p.relative_to(app).as_posix() not in expected]
assert all('__pycache__' in p.relative_to(app).parts and p.suffix=='.pyc' and p.resolve().is_relative_to(app) for p in extra), 'Unexpected modified content: stop'
for p in extra:p.unlink()
for p in sorted(app.rglob('__pycache__'),key=lambda p:len(p.parts),reverse=True):
 if p.resolve().is_relative_to(app) and not any(p.iterdir()):p.rmdir()
print('Removed generated validation bytecode only:',len(extra))
