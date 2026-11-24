import json,subprocess,sys,os
from pathlib import Path
ROOT=Path(__file__).resolve().parents[1];OUT=ROOT/'artifacts/validation/v1.8.1'
rows=json.loads((OUT/'regressions.json').read_text())
for row in rows:
 if row['returncode']==0:continue
 name=row['case'];p=subprocess.run([sys.executable,'-X','utf8',str(ROOT/'tools'/f'{name}.py')],cwd=ROOT,capture_output=True,text=True,encoding='utf8',env=dict(os.environ,PYTHONIOENCODING='utf-8'),timeout=180)
 (OUT/(name+'-retry.log')).write_text(p.stdout+p.stderr,encoding='utf8');row['initial_returncode']=row['returncode'];row['returncode']=p.returncode;print(name,p.returncode,flush=True)
(OUT/'regressions.json').write_text(json.dumps(rows,indent=2))
raise SystemExit(any(r['returncode'] for r in rows))
