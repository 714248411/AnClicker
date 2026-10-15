
import os, subprocess, sys
from pathlib import Path

def main():
    root=Path(__file__).resolve().parents[1]
    subprocess.run([sys.executable, str(root/'tools/import_policy.py')], cwd=root, check=True)
    (root/'artifacts/validation').mkdir(parents=True, exist_ok=True)
    env=dict(os.environ)
    windows=Path(env.get('SystemRoot','C:/Windows'))
    env['PATH']=os.pathsep.join(map(str,[Path(sys.executable).parent,Path(sys.base_prefix),windows/'System32',windows]))
    with (root/'artifacts/validation'/'local-build.log').open('w',encoding='utf-8') as log:
        subprocess.run([sys.executable,'-m','PyInstaller',*(['--clean'] if '--clean' in sys.argv else []),'-y','--distpath',str(root/'artifacts/dist/local-test'),'--workpath',str(root/'artifacts/build/local-test'),str(root/'tools/packaging/main.spec')],cwd=root,env=env,stdout=log,stderr=subprocess.STDOUT,check=True)
    print('Built artifacts/dist/local-test/AnClicker')
    

if __name__ == '__main__':
    main()
