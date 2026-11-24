import subprocess,sys,json,time
from pathlib import Path
root=Path(__file__).resolve().parents[1];out=root/'artifacts/debug/model-chain'
cases=['tools/check_model_chain.py','tools/check_colloquial_sheet.py','tools/check_dialogue_sheet_roundtrip.py','tools/check_draft_verification.py','tools/check_simple_language.py','tools/check_model_chain_language.py','tools/check_api_parity.py']
results=[]
for name in cases:
 start=time.monotonic();print('START',name,flush=True)
 with (out/(Path(name).stem+'.log')).open('w',encoding='utf8') as log:
  try:r=subprocess.run([sys.executable,'-X','utf8',name],cwd=root,stdout=log,stderr=subprocess.STDOUT,timeout=420);code=r.returncode
  except subprocess.TimeoutExpired:code='timeout'
 results.append({'test':name,'exit_code':code,'seconds':round(time.monotonic()-start,2)})
 (out/'regression.json').write_text(json.dumps(results,indent=2),encoding='utf8')
 print('DONE',results[-1],flush=True)
print('ALL_PASS' if all(r['exit_code']==0 for r in results) else 'FAILED',flush=True)
