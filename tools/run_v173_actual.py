import sys,subprocess,json
from pathlib import Path
ROOT=Path(__file__).resolve().parents[1];OUT=ROOT/'artifacts/debug/v173-retest';rows=[]
for name in ['check_v173_actual','check_v173_api']:
 with (OUT/(name+'.log')).open('w',encoding='utf8') as log:
  r=subprocess.run([sys.executable,'-X','utf8','tools/'+name+'.py'],cwd=ROOT,stdout=log,stderr=subprocess.STDOUT,timeout=180)
 rows.append({'test':name,'exit_code':r.returncode});print(rows[-1],flush=True)
(OUT/'actual-run.json').write_text(json.dumps(rows,indent=2),encoding='utf8')
