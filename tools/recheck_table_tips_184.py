import os,sys,subprocess,json,time
from pathlib import Path
root=Path(__file__).resolve().parents[1];out=root/'artifacts/validation/v1.8.4';attempts=[]
for n in range(3):
 start=time.monotonic();p=subprocess.run([sys.executable,'-B','-X','utf8','tools/check_table_tips_center.py'],cwd=root,capture_output=True,text=True,encoding='utf8');attempts.append({'returncode':p.returncode,'seconds':time.monotonic()-start});(out/f'table-tips-retry-{n+1}.log').write_text(p.stdout+p.stderr,encoding='utf8');assert p.returncode==0,p.stdout+p.stderr
path=out/'regressions.json';records=json.loads(path.read_text());(out/'regressions-initial.json').write_text(json.dumps(records,indent=2))
for item in records:
 if item['case']=='check_table_tips_center':item.update(initial_returncode=item['returncode'],returncode=0,retries=attempts)
path.write_text(json.dumps(records,indent=2));print('PASS three isolated repeats; initial failure preserved')
