import subprocess,sys,json
from pathlib import Path
ROOT=Path(__file__).resolve().parents[1];OUT=ROOT/'artifacts/debug/v173-retest'
for args in ([],['extra']):
 with (OUT/('retrieval-extra.log' if args else 'retrieval.log')).open('w',encoding='utf8') as log:
  r=subprocess.run([sys.executable,'-X','utf8','tools/check_v173_retrieval.py',*args],cwd=ROOT,stdout=log,stderr=subprocess.STDOUT,timeout=600)
 print(args,r.returncode,flush=True)
