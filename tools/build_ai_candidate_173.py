"""Build an isolated local candidate; leave published 1.7.3 artifacts untouched."""
import os,sys,subprocess,json
from pathlib import Path
ROOT=Path(__file__).resolve().parents[1];sys.path.insert(0,str(ROOT))
OUT=ROOT/'artifacts/debug/v173-optimize'
env=dict(os.environ);windows=Path(env.get('SystemRoot','C:/Windows'))
env['PATH']=os.pathsep.join(map(str,[Path(sys.executable).parent,Path(sys.base_prefix),windows/'System32',windows]))
subprocess.run([sys.executable,'-m','PyInstaller','-y','--distpath',str(ROOT/'artifacts/dist/v1.7.3-ai-candidate'),'--workpath',str(ROOT/'artifacts/build/v1.7.3-ai-candidate'),str(ROOT/'tools/packaging/main.spec')],cwd=ROOT,env=env,check=True)
import tools.package_release_173 as package
package.DIST=ROOT/'artifacts/dist/v1.7.3-ai-candidate/AnClicker'
package.stage()
print('CANDIDATE_READY',package.DIST,flush=True)
