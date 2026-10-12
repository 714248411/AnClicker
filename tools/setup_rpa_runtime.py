"""Install the pinned Electron runtime locally; never modify the source project."""
import argparse
import hashlib
from pathlib import Path
import shutil
import sys
import tempfile
import urllib.request
import zipfile
VERSION='31.7.7'
root=Path(__file__).resolve().parents[1]
parser=argparse.ArgumentParser()
parser.add_argument('--from-directory',type=Path,help='Existing Electron dist directory (offline copy)')
args=parser.parse_args()
target=root/'runtime/electron'
if args.from_directory:
    if not (args.from_directory/'electron.exe').is_file():
        raise SystemExit('Source must contain electron.exe')
    shutil.copytree(args.from_directory,target,dirs_exist_ok=True)
else:
    if sys.platform!='win32':
        raise SystemExit('Set ANCLICKER_ELECTRON to an Electron 31 runtime for this platform.')
    name=f'electron-v{VERSION}-win32-x64.zip'
    base=f'https://github.com/electron/electron/releases/download/v{VERSION}/'
    checksums=urllib.request.urlopen(base+'SHASUMS256.txt',timeout=60).read().decode()
    expected=next(line.split()[0] for line in checksums.splitlines() if line.split()[-1]==name)
    with tempfile.TemporaryDirectory() as temp:
        archive=Path(temp)/name
        urllib.request.urlretrieve(base+name,archive)
        if hashlib.sha256(archive.read_bytes()).hexdigest()!=expected:
            raise SystemExit('Electron checksum mismatch')
        target.mkdir(parents=True,exist_ok=True)
        with zipfile.ZipFile(archive) as z:
            for entry in z.infolist():
                resolved=(target/entry.filename).resolve()
                if not resolved.is_relative_to(target.resolve()):
                    raise SystemExit('Invalid archive path')
            z.extractall(target)
print(target)
