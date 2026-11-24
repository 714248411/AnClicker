import os,sys,zipfile,json
from pathlib import Path
ROOT=Path(__file__).resolve().parents[1];sys.path.insert(0,str(ROOT))
from tools.publishing_credentials import publishing_environment
from info import UPDATE_CONFIG
env=publishing_environment('F:/下载/开机安装/AnClicker七牛云环境变量配置.txt',os.environ,UPDATE_CONFIG)
keys=[env.get(UPDATE_CONFIG[k],'').encode() for k in ('access_key_env','secret_key_env')]
with zipfile.ZipFile(ROOT/'artifacts/source/v1.8.7/AnClicker-v1.8.7-win-DaiMa.zip') as z:
 matches=[n for n in z.namelist() if any(k and k in z.read(n) for k in keys)]
 assert not matches,'Sensitive content found; do not publish'
 assert z.testzip() is None
 print('PASS source archive contains no configured publishing credentials; CRC valid')
