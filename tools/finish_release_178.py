import subprocess,sys
from pathlib import Path
root=Path(__file__).resolve().parents[1]
for name,args in [('package_release_178',['--stage']),('smoke_release_178',[]),('package_source_178',[]),('package_release_178',[]),('verify_release_178_artifacts',[])]:
 print('START',name,*args,flush=True)
 subprocess.run([sys.executable,'-X','utf8',str(root/'tools'/(name+'.py')),*args],cwd=root,check=True)
 print('PASS',name,flush=True)
