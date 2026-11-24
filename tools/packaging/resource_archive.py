"""Validate expanded release assets; retain the old archive utility for legacy checks."""
import argparse
import json
import os
from pathlib import Path
import sys
import zipfile
if __package__ in (None, ''):
    sys.path.insert(0, str(Path(__file__).resolve().parents[2]))
from anclicker.app.resource_bundle import ARCHIVE, MANIFEST, STATE, PREFIXES, allowed, digest, destination


def require_expanded_resources(app):
    """Reject old nested-resource builds before creating a single-extraction ZIP."""
    app = Path(app)
    if any((app / name).exists() for name in (ARCHIVE, MANIFEST)):
        raise RuntimeError('构建目录含旧版内部资源压缩包，请重新构建完整展开的程序后再打包。')


def pack_resources(app):
    app = Path(app).resolve()
    # Never retrofit an already-published executable: it lacks the runtime hook.
    if not (app / 'resource-bootstrap-v1').is_file():
        raise RuntimeError('请先重新构建含资源启动钩子的程序，不可修改旧版发布包。')
    if (app / ARCHIVE).exists() or (app / MANIFEST).exists():
        raise FileExistsError('资源包已存在，请使用新的构建目录')
    paths = []
    for prefix in PREFIXES:
        for path in sorted((app / prefix).rglob('*')):
            if path.is_file() and allowed(path.relative_to(app).as_posix()):
                destination(app, path.relative_to(app).as_posix())
                paths.append(path)
    if not paths:
        raise ValueError('未找到模型或业务运行库')
    records = {}
    partial = app / (ARCHIVE + '.partial')
    with zipfile.ZipFile(partial, 'x', compression=zipfile.ZIP_DEFLATED, compresslevel=6, allowZip64=True) as archive:
        for path in paths:
            name = path.relative_to(app).as_posix()
            records[name] = {'size': path.stat().st_size, 'sha256': digest(path)}
            archive.write(path, name)
    # Verify compressed bytes against the original hashes before removing files.
    import hashlib
    with zipfile.ZipFile(partial) as archive:
        for name, item in records.items():
            value = hashlib.sha256()
            with archive.open(name) as reader:
                for chunk in iter(lambda: reader.read(1024 * 1024), b''):
                    value.update(chunk)
            if value.hexdigest() != item['sha256']:
                raise RuntimeError('压缩校验失败：' + name)
    temp = app / (MANIFEST + '.partial')
    temp.write_text(json.dumps({'schema': 1, 'files': records}, ensure_ascii=False, sort_keys=True), encoding='utf-8')
    os.replace(partial, app / ARCHIVE)
    os.replace(temp, app / MANIFEST)
    for path in paths:
        if digest(path) != records[path.relative_to(app).as_posix()]['sha256']:
            raise RuntimeError('资源在压缩期间发生变化：' + str(path))
    for path in paths:
        path.unlink()
    (app / STATE).unlink(missing_ok=True)
    return {'files': len(records), 'original_bytes': sum(v['size'] for v in records.values()),
            'archive_bytes': (app / ARCHIVE).stat().st_size}


if __name__ == '__main__':
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--app', type=Path, required=True)
    args = parser.parse_args()
    print(json.dumps(pack_resources(args.app), ensure_ascii=False))
