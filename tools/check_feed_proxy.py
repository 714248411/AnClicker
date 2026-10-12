import sys,json
from pathlib import Path
root=Path(__file__).resolve().parents[1];sys.path.insert(0,str(root/'.runtime-tools'))
import requests
try:
    r=requests.get('https://updates.ytsoftware.cn/an-clicker/win-x64/releases.win-x64.json',timeout=(15,45));r.raise_for_status()
    feed=r.json();(root/'validation/remote-feed.json').write_text(json.dumps(feed),encoding='utf-8')
    print('Public versions:',sorted({a['Version'] for a in feed['Assets']}))
except Exception as e:
    print(type(e).__name__+': '+str(e));raise SystemExit(1)
