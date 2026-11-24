"""Build in an isolated version directory without changing prior artifacts."""
import os,subprocess,sys,json,time
from pathlib import Path
ROOT=Path(__file__).resolve().parents[1]
OUT=ROOT/'artifacts/validation/v1.9.0'
assert json.loads((OUT/'models.json').read_text(encoding='utf8'))['live_checks']
# Candidate build; final packaging independently requires all regression checks.
env=dict(os.environ)
windows=Path(env.get('SystemRoot','C:/Windows'))
env['PATH']=os.pathsep.join(map(str,[Path(sys.executable).parent,Path(sys.base_prefix),windows/'System32',windows]))
start=time.time()
with (OUT/'build.log').open('w',encoding='utf8') as log:
 subprocess.run([sys.executable,'-m','PyInstaller','-y','--distpath',str(ROOT/'artifacts/dist/v1.9.0'),'--workpath',str(ROOT/'artifacts/build/v1.9.0'),str(ROOT/'tools/packaging/main.spec')],cwd=ROOT,env=env,stdout=log,stderr=subprocess.STDOUT,check=True)
(OUT/'build.json').write_text(json.dumps({'version':'1.9.0','passed':True,'seconds':time.time()-start}))
print('PASS v1.9.0 application build',flush=True)
