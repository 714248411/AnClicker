import sys
from pathlib import Path
root=Path(__file__).resolve().parents[1];sys.path.insert(0,str(root));sys.path.insert(0,str(root/'tools/packaging'))
import anclicker
from tools.packaging.发布门槛 import _check_member
app=root/'artifacts/dist/v1.8.2/AnClicker';bad=[]
for p in app.rglob('*'):
 try:_check_member(p.relative_to(app).as_posix())
 except RuntimeError:bad.append(p.relative_to(app).as_posix())
print('rejected count',len(bad));print('\n'.join(sorted(set('/'.join(p.split('/')[:7]) for p in bad))))
