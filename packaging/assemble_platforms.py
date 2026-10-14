"""Combine native packages while preserving their symlinks and permissions."""
import copy
import hashlib
import json
from pathlib import Path
import shutil
import zipfile

root = Path('platform-artifacts')
out = Path('delivery')
out.mkdir(exist_ok=True)
version = 'v1.6.1'
with zipfile.ZipFile(out / f'AnClicker-{version}-mac.zip', 'w') as archive:
    for arch, folder in [('x64', 'Intel'), ('arm64', 'Apple-Silicon')]:
        source = root / f'package-macos-{arch}' / f'AnClicker-{version}-macos-{arch}.zip'
        with zipfile.ZipFile(source) as native:
            assert native.testzip() is None
            for member in native.infolist():
                item = copy.copy(member)
                item.filename = folder + '/' + member.filename
                archive.writestr(item, native.read(member))
    archive.writestr('使用说明.txt', Path('packaging/PLATFORM_GUIDE.md').read_bytes())
shutil.copyfile(root / 'package-linux-x64' / f'AnClicker-{version}-linux-x64.zip',
                out / f'AnClicker-{version}-linux.zip')
checksums = {}
for package in out.glob('*.zip'):
    with zipfile.ZipFile(package) as archive:
        assert archive.testzip() is None
    checksums[package.name] = hashlib.file_digest(package.open('rb'), 'sha256').hexdigest()
(out / 'SHA256.json').write_text(json.dumps(checksums, indent=2))
