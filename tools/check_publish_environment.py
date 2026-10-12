import os,json,urllib.request
from pathlib import Path
print('credentials_present='+str(all(os.environ.get(k) for k in ('QINIU_ACCESS_KEY','QINIU_SECRET_KEY'))),flush=True)
root=Path(__file__).resolve().parents[1]
with urllib.request.build_opener(urllib.request.ProxyHandler({})).open('https://updates.ytsoftware.cn/an-clicker/win-x64/releases.win-x64.json',timeout=30) as response:
    feed=json.load(response);(root/'validation/remote-feed.json').write_text(json.dumps(feed),encoding='utf-8')
print('public_versions='+str(sorted({a['Version'] for a in feed['Assets']})))
