import sys
from pathlib import Path
sys.path.insert(0,str(Path(__file__).resolve().parents[1]))
from tools.packaging.发布门槛 import _check_member
for p in ('runtime/crawl4ai/python/Lib/site-packages/fake_useragent/data/browsers.jsonl','current/runtime/crawl4ai/python/Lib/site-packages/numpy/random/tests/data/example.csv'):_check_member(p)
for p in ('Data/user.png','current/Data/user.png','lib/app/Data/user.png','runtime/crawl4ai/profiles/user.json','runtime/crawl4ai/python/Lib/site-packages/unknown/data/user.db'):
 try:_check_member(p)
 except RuntimeError:pass
 else:raise AssertionError(p)
print('PASS readonly dependency datasets allowed, user Data/profiles remain forbidden')

import tempfile
from tools.packaging.发布门槛 import validate_directory
with tempfile.TemporaryDirectory() as td:
 root=Path(td);(root/'Data').mkdir();validate_directory(root)
 (root/'Data'/'user.png').write_bytes(b'user')
 try:validate_directory(root)
 except RuntimeError:pass
 else:raise AssertionError('User data accepted')
print('PASS empty Data allowed, non-empty Data rejected')
