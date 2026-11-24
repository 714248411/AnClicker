from pathlib import Path
import zipfile
root=Path(__file__).resolve().parents[1];app=root/'artifacts/dist/v1.8.3/AnClicker'
with zipfile.ZipFile(root/'artifacts/release/v1.8.3-qiniu/AnClicker-1.8.3-win-x64-full.nupkg') as z:
 names={n[8:]:n for n in z.namelist() if n.startswith('lib/app/') and not n.endswith('/')}
 actual={p.relative_to(app).as_posix():p for p in app.rglob('*') if p.is_file()}
 print('added',sorted(set(actual)-set(names)))
 changed=[]
 for n,p in actual.items():
  if n in names and (p.stat().st_size!=z.getinfo(names[n]).file_size or p.read_bytes()!=z.read(names[n])):changed.append(n)
 print('changed',changed)
