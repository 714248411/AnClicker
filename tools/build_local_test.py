def main():
    import os, subprocess, sys
    from pathlib import Path
    root=Path(__file__).resolve().parents[1]
    env=dict(os.environ)
    windows=Path(env.get('SystemRoot','C:/Windows'))
    env['PATH']=os.pathsep.join(map(str,[Path(sys.executable).parent,Path(sys.base_prefix),windows/'System32',windows]))
    with (root/'validation'/'local-build.log').open('w',encoding='utf-8') as log:
        subprocess.run([sys.executable,'-m','PyInstaller',*(['--clean'] if '--clean' in sys.argv else []),'-y','--distpath',str(root/'dist/local-test'),'--workpath',str(root/'build/local-test'),str(root/'packaging/main.spec')],cwd=root,env=env,stdout=log,stderr=subprocess.STDOUT,check=True)
    print('Built dist/local-test/AnClicker')
    

if __name__ == '__main__':
    main()
