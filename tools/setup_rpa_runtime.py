"""Install the pinned Electron runtime locally; never modify the source project."""
import argparse
import hashlib
from pathlib import Path
import shutil
import sys
import tempfile
import urllib.request
import zipfile
import platform
import subprocess
VERSION='31.7.7'
root=Path(__file__).resolve().parents[1]
parser=argparse.ArgumentParser()
parser.add_argument('--from-directory',type=Path,help='Existing Electron dist directory (offline copy)')
args=parser.parse_args()
target=root/'.local/runtimes/electron'
entry = ('Electron.app/Contents/MacOS/Electron' if sys.platform == 'darwin'
         else 'electron.exe' if sys.platform == 'win32' else 'electron')
if args.from_directory:
    if not (args.from_directory/entry).is_file():
        raise SystemExit(f'Source must contain {entry}')
    shutil.copytree(args.from_directory,target,dirs_exist_ok=True,symlinks=True)
else:
    system = {'win32': 'win32', 'darwin': 'darwin', 'linux': 'linux'}.get(sys.platform)
    arch = {'AMD64': 'x64', 'x86_64': 'x64', 'arm64': 'arm64', 'aarch64': 'arm64'}.get(platform.machine())
    if not system or not arch:
        raise SystemExit('Unsupported Electron platform or architecture')
    name=f'electron-v{VERSION}-{system}-{arch}.zip'
    base=f'https://github.com/electron/electron/releases/download/v{VERSION}/'
    checksums=urllib.request.urlopen(base+'SHASUMS256.txt',timeout=60).read().decode()
    expected=next(line.split()[0] for line in checksums.splitlines()
                  if len(line.split()) == 2 and line.split()[-1].lstrip('*') == name)
    with tempfile.TemporaryDirectory() as temp:
        archive=Path(temp)/name
        urllib.request.urlretrieve(base+name,archive)
        if hashlib.sha256(archive.read_bytes()).hexdigest()!=expected:
            raise SystemExit('Electron checksum mismatch')
        target.mkdir(parents=True,exist_ok=True)
        with zipfile.ZipFile(archive) as z:
            for member in z.infolist():
                resolved=(target/member.filename).resolve()
                if not resolved.is_relative_to(target.resolve()):
                    raise SystemExit('Invalid archive path')
            if sys.platform == 'win32':
                z.extractall(target)
            else:
                # Preserve executable permissions and macOS framework symlinks.
                subprocess.run(['unzip', '-q', str(archive), '-d', str(target)], check=True)
if not (target/entry).is_file():
    raise SystemExit(f'Missing runtime entry: {entry}')
print(target)
