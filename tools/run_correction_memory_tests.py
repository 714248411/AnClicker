import sys,subprocess,json,time
from pathlib import Path
ROOT=Path(__file__).resolve().parents[1];OUT=ROOT/'artifacts/debug/correction-memory'
group=sys.argv[1]
cases=([['tools/check_correction_memory_retrieval.py'],['tools/check_correction_memory_retrieval.py','extra']] if group=='retrieval' else [['tools/check_correction_memory_generation.py'],['tools/check_correction_memory_heldout.py'],['tools/check_colloquial_expanded_actual.py'],['tools/check_api_parity.py'],['tools/check_draft_verification.py']])
rows=[]
for args in cases:
 name=Path(args[0]).stem+('-extra' if len(args)>1 else '');start=time.monotonic();print('START',name,flush=True)
 with (OUT/(name+'.log')).open('w',encoding='utf8') as log:
  try:result=subprocess.run([sys.executable,'-X','utf8',*args],cwd=ROOT,stdout=log,stderr=subprocess.STDOUT,timeout=600);code=result.returncode
  except subprocess.TimeoutExpired:code='timeout'
 rows.append({'test':name,'exit_code':code,'seconds':round(time.monotonic()-start,2)});(OUT/(group+'-run.json')).write_text(json.dumps(rows,indent=2),encoding='utf8');print('DONE',rows[-1],flush=True)
