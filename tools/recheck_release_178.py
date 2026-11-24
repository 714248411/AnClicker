import json,subprocess,sys,time,os
from pathlib import Path
ROOT=Path(__file__).resolve().parents[1]
OUT=ROOT/'artifacts/validation/v1.7.8'
rows=json.loads((OUT/'regressions.json').read_text())
for row in rows:
 if row['case']=='check_blank_recent':row['case']='check_new_blank_full_window'
 if row['returncode'] or row['case'] in ('check_tooltip_policy','check_dynamic_left'):
  start=time.perf_counter()
  r=subprocess.run([sys.executable,'-X','utf8',str(ROOT/'tools'/(row['case']+'.py'))],cwd=ROOT,capture_output=True,encoding='utf8',errors='replace',timeout=180,env=dict(os.environ,QT_QPA_PLATFORM='offscreen'))
  (OUT/(row['case']+'.log')).write_text(r.stdout+r.stderr,encoding='utf8')
  row.update(returncode=r.returncode,seconds=time.perf_counter()-start)
  print(row['case'],r.returncode,flush=True)
(OUT/'regressions.json').write_text(json.dumps(rows,indent=2))
assert len(rows)==72 and all(r['returncode']==0 for r in rows)
