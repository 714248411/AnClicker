import subprocess,sys,json,time
from pathlib import Path
ROOT=Path(__file__).resolve().parents[1];OUT=ROOT/'artifacts/debug/v173-retest';rows=[]
for label in ['release','workspace']:
 with (OUT/(label+'-language.log')).open('w',encoding='utf8') as log:
  start=time.monotonic();r=subprocess.run([sys.executable,'-X','utf8','tools/check_v173_language.py',label],cwd=ROOT,stdout=log,stderr=subprocess.STDOUT,timeout=900)
 rows.append({'label':label,'exit_code':r.returncode,'seconds':round(time.monotonic()-start,2)});print(rows[-1],flush=True)
 (OUT/'language-run.json').write_text(json.dumps(rows,indent=2),encoding='utf8')
