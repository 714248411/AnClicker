import subprocess,sys,time,json,psutil
from pathlib import Path
ROOT=Path(__file__).resolve().parents[1];OUT=ROOT/'artifacts/validation/v1.8.7'
while psutil.pid_exists(18700): time.sleep(2)
assert json.loads((OUT/'upgrade.json').read_text())['passed']
assert (ROOT/'artifacts/source/v1.8.7/AnClicker-v1.8.7-win-DaiMa.zip.sha256').is_file()
credential='F:/下载/开机安装/AnClicker七牛云环境变量配置.txt'
for name,args in [('qiniu-publish',['tools/qiniu_release_187.py','publish',credential]),('qiniu-delivery',['tools/publish_qiniu_delivery_187.py',credential]),('public-client',['tools/check_public_update_187.py'])]:
 print('START '+name,flush=True)
 with (OUT/(name+'.log')).open('w',encoding='utf8') as log:
  subprocess.run([sys.executable,'-B','-X','utf8',*args],cwd=ROOT,stdout=log,stderr=subprocess.STDOUT,check=True)
 print('PASS '+name,flush=True)
