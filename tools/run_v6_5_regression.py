import sys,subprocess,json,time
from pathlib import Path
ROOT=Path(__file__).resolve().parents[1];OUT=ROOT/'artifacts/debug/multi-task-v6_5'
jobs=[['tools/check_multi_task_v6_5.py','v6_5'],['tools/check_online_operations.py','v6_5','--candidate','--model-version','v6_5'],['tools/check_online_operations.py','v6_5-unseen','--candidate','--unseen','--model-version','v6_5'],['tools/check_long_sentences_v2.py','v6_5','--candidate','--model-version','v6_5'],['models/training/evaluate_v6_4_roles.py','--model-version','v6_5'],['tools/check_spreadsheet_web_language.py'],['tools/check_spreadsheet_web_roundtrip.py']]
rows=[]
for args in jobs:
 print('RUN',args,flush=True);result=subprocess.run([sys.executable,'-X','utf8','-u',*args],cwd=ROOT)
 rows.append({'args':args,'returncode':result.returncode});(OUT/'regression-processes.json').write_text(json.dumps(rows,ensure_ascii=False,indent=2),encoding='utf8')
print('V6_5_REGRESSION_COMPLETE',flush=True)
