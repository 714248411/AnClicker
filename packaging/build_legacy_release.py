"""Create a separate Qt5 package; never relabel a Python 3.12 build as legacy."""
import hashlib
import json
from pathlib import Path
import subprocess
import sys
import zipfile

ROOT = Path(__file__).resolve().parents[1]

def main():
    if sys.platform != 'win32' or sys.version_info[:2] != (3, 10):
        raise RuntimeError('Legacy release must be built on Windows with Python 3.10')
    from PyQt5.QtCore import QT_VERSION_STR, PYQT_VERSION_STR
    if QT_VERSION_STR != '5.15.2' or PYQT_VERSION_STR != '5.15.10':
        raise RuntimeError('Unexpected Qt/PyQt build version')
    subprocess.run([sys.executable, str(ROOT/'packaging/build_release.py'),
                    '--version', 'v1.2.6'], check=True, cwd=ROOT)
    release = ROOT/'release'
    package = release/'AnClicker-v1.2.6-windows-x64.zip'
    target = release/'AnClicker-v1.2.6-windows-x64-pyqt5-legacy.zip'
    package.rename(target)
    with zipfile.ZipFile(target, 'a', compression=zipfile.ZIP_DEFLATED) as archive:
        for name in ('LICENSE', 'LEGACY_WINDOWS.md', 'THIRD_PARTY_LEGACY.md', 'COPYING-GPL-3.0.txt'):
            archive.write(ROOT/name, 'AnClicker/'+name)
        archive.writestr('LEGACY-EDITION.json', json.dumps({
            'edition':'pyqt5-legacy', 'version':'v1.2.6',
            'python':sys.version, 'qt':QT_VERSION_STR, 'pyqt':PYQT_VERSION_STR,
            'target':'Windows 10 1607 x64', 'target_os_verified':False,
        }, indent=2))
    source = release/'AnClicker-v1.2.6-pyqt5-legacy-source.zip'
    subprocess.run(['git','archive','--format=zip','--prefix=AnClicker-source/',
                    '-o',str(source),'HEAD'], check=True,cwd=ROOT)
    sums=[]
    for path in (target, source):
        sums.append(hashlib.sha256(path.read_bytes()).hexdigest()+'  '+path.name)
    (release/'SHA256SUMS.txt').write_text('\n'.join(sums)+'\n',encoding='utf-8')

if __name__ == '__main__':
    main()
