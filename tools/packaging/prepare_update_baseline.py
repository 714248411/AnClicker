"""Prepare runtime inputs and an isolated legacy portable from the 1.9.2 release."""
import argparse
from hashlib import sha256
from pathlib import Path, PurePosixPath
import shutil
import sys
from zipfile import ZipFile

ROOT = Path(__file__).resolve().parents[2]
if str(ROOT) not in sys.path:
    sys.path.insert(0, str(ROOT))
from anclicker.app.resource_bundle import ensure_resources

BASELINE_SHA256 = '1ed64c5a9f404d166bfb0b72b45ec79fd4faedeb33c87037bb49cfdacb60d6b9'


def prepare(archive_path, destination):
    digest = sha256()
    with archive_path.open('rb') as stream:
        for chunk in iter(lambda: stream.read(1024 * 1024), b''):
            digest.update(chunk)
    if digest.hexdigest() != BASELINE_SHA256:
        raise ValueError('The 1.9.2 Windows ZIP failed SHA-256 verification')
    with ZipFile(archive_path) as archive:
        destinations = set()
        for member in archive.infolist():
            name = PurePosixPath(member.filename)
            if (name.is_absolute() or any(
                    part in ('.', '..') or ':' in part or chr(92) in part or part.endswith(('.', ' '))
                    for part in name.parts)):
                raise ValueError(f'Invalid path in baseline: {member.filename}')
            key = name.as_posix().casefold()
            if key in destinations:
                raise ValueError(f'Duplicate path in baseline: {member.filename}')
            destinations.add(key)
        destination.mkdir(parents=True)
        archive.extractall(destination)
    installed = list(destination.rglob('current/sq.version'))
    if len(installed) != 1 or not (installed[0].parent.parent / 'Update.exe').is_file():
        raise ValueError('The baseline must be an AnClicker Velopack portable')
    app = installed[0].parent
    ensure_resources(app, verify=True)
    inputs = {
        'models/embeddings/bge-small-zh-v1.5/model.onnx': 'models/embeddings/bge-small-zh-v1.5/model.onnx',
        'resources/background/dll/xd47243.dll': 'resources/background/dll/xd47243.dll',
        'resources/background/dll/Go.dll': 'resources/background/dll/Go.dll',
    }
    for source, target in inputs.items():
        path = ROOT / target
        if path.exists():
            if sha256(path.read_bytes()).digest() != sha256((app / source).read_bytes()).digest():
                raise ValueError(f'Existing build input differs from the baseline: {target}')
        else:
            path.parent.mkdir(parents=True, exist_ok=True)
            shutil.copy2(app / source, path)
    electron = ROOT / '.local/runtimes/electron'
    if not electron.exists():
        shutil.copytree(app / 'runtime/electron', electron)
    return app


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('archive', type=Path)
    parser.add_argument('destination', type=Path)
    args = parser.parse_args()
    print(prepare(args.archive.resolve(), args.destination.resolve()))


if __name__ == '__main__':
    main()
