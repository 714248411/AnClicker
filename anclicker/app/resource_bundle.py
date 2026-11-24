"""Restore packaged assets before application/native-library imports.

Only release-owned files are allowed. User Data and bootstrap dependencies are
never members. The zip is retained so a missing resource can be repaired offline.
"""
from contextlib import contextmanager
import hashlib
import json
import os
from pathlib import Path, PurePosixPath
import stat
import sys
import tempfile
import time
import zipfile

ARCHIVE = 'AnClicker-resources.zip'
MANIFEST = 'AnClicker-resources.json'
STATE = '.anclicker-resources-state.json'
PREFIXES = ('models/', 'ocr_models/', 'resources/background/', 'runtime/electron/')


def allowed(name):
    path = PurePosixPath(name)
    return (isinstance(name, str) and name.startswith(PREFIXES)
            and not (path.parent == PurePosixPath('models') and path.suffix.lower() == '.json')
            and path.suffix.lower() not in ('.log', '.db', '.sqlite', '.sqlite3')
            and not path.is_absolute() and '\\' not in name and ':' not in name
            and all(p not in ('', '.', '..') for p in name.split('/'))
            and path.suffix.lower() not in ('.py', '.pyc', '.pyo')
            and not any(p.startswith('.') for p in path.parts))


def digest(path):
    value = hashlib.sha256()
    with Path(path).open('rb') as stream:
        for chunk in iter(lambda: stream.read(1024 * 1024), b''):
            value.update(chunk)
    return value.hexdigest()


def destination(root, name):
    if not allowed(name):
        raise ValueError('不允许的资源路径：' + str(name))
    target = root / name
    # Reject links/junctions, including an existing destination file.
    for part in (target, *target.parents):
        if part == root:
            break
        if part.is_symlink() or (part.exists() and
                getattr(part.lstat(), 'st_file_attributes', 0) & 0x400):
            raise ValueError('资源路径不能包含链接：' + name)
    target.resolve().relative_to(root.resolve())
    return target


@contextmanager
def bundle_lock(root, timeout=600):
    lock = (root / '.anclicker-resources.lock').open('a+b')
    lock.seek(0, 2)
    if lock.tell() == 0:
        lock.write(b'0'); lock.flush()
    end = time.monotonic() + timeout
    try:
        while True:
            try:
                lock.seek(0)
                if os.name == 'nt':
                    import msvcrt
                    msvcrt.locking(lock.fileno(), msvcrt.LK_NBLCK, 1)
                else:
                    import fcntl
                    fcntl.flock(lock, fcntl.LOCK_EX | fcntl.LOCK_NB)
                break
            except OSError:
                if time.monotonic() >= end:
                    raise TimeoutError('正在释放程序资源，请稍后重新启动。')
                time.sleep(.1)
        yield
    finally:
        lock.close()  # OS releases the lock even after a crash.


def _stamp(path):
    st = path.stat()
    return [st.st_size, st.st_mtime_ns]


def ensure_resources(root, *, verify=False, progress=None):
    root = Path(root).resolve()
    manifest_path = root / MANIFEST
    if not manifest_path.exists():
        if (root / ARCHIVE).exists():
            raise RuntimeError('资源清单缺失，请重新解压完整程序包。')
        return {'restored': 0, 'checked': 0}
    raw = manifest_path.read_bytes()
    manifest = json.loads(raw)
    files = manifest.get('files', {})
    if manifest.get('schema') != 1 or not isinstance(files, dict) or not files:
        raise ValueError('资源清单无效')
    for name, item in files.items():
        destination(root, name)
        if (not isinstance(item, dict) or type(item.get('size')) is not int
                or item['size'] < 0 or len(item.get('sha256', '')) != 64):
            raise ValueError('资源清单条目无效：' + name)
    identity = hashlib.sha256(raw).hexdigest()
    with bundle_lock(root):
        try:
            state = json.loads((root / STATE).read_text(encoding='utf-8'))
        except (OSError, ValueError):
            state = {}
        stamps = state.get('files', {}) if state.get('identity') == identity else {}
        pending, actual = [], {}
        for name, item in files.items():
            target = destination(root, name)
            if target.is_file() and target.stat().st_size == item['size']:
                stamp = _stamp(target)
                if (not verify and stamps.get(name) == stamp) or digest(target) == item['sha256']:
                    actual[name] = stamp
                    continue
            pending.append(name)
        if pending:
            archive_path = root / ARCHIVE
            if not archive_path.is_file():
                raise RuntimeError('内置资源压缩包缺失，无法修复：' + ARCHIVE)
            with zipfile.ZipFile(archive_path) as archive:
                infos = archive.infolist()
                if len({i.filename for i in infos}) != len(infos):
                    raise ValueError('资源压缩包包含重复条目')
                if {i.filename for i in infos} != set(files):
                    raise ValueError('资源压缩包与清单不一致')
                # Stage every required file before publishing any of them.
                with tempfile.TemporaryDirectory(prefix='.ac-resource-stage-', dir=root) as stage:
                    for index, name in enumerate(pending):
                        info = archive.getinfo(name)
                        if (info.file_size != files[name]['size'] or
                                stat.S_ISLNK(info.external_attr >> 16)):
                            raise ValueError('资源条目无效：' + name)
                        staged = Path(stage) / name
                        staged.parent.mkdir(parents=True, exist_ok=True)
                        value = hashlib.sha256()
                        with archive.open(info) as reader, staged.open('wb') as writer:
                            for chunk in iter(lambda: reader.read(1024 * 1024), b''):
                                writer.write(chunk); value.update(chunk)
                        if value.hexdigest() != files[name]['sha256']:
                            raise ValueError('资源校验失败：' + name)
                        if progress:
                            progress(index + 1, len(pending), name)
                    for name in pending:
                        target = destination(root, name)
                        target.parent.mkdir(parents=True, exist_ok=True)
                        os.replace(Path(stage) / name, target)
                        actual[name] = _stamp(target)
        if pending or state.get('identity') != identity or stamps != actual:
            temp = root / (STATE + '.tmp')
            temp.write_text(json.dumps({'identity': identity, 'files': actual}), encoding='utf-8')
            os.replace(temp, root / STATE)
        return {'restored': len(pending), 'checked': len(files)}


def bootstrap():
    if not getattr(sys, 'frozen', False) or '--update-worker' in sys.argv:
        return
    root = Path(getattr(sys, '_MEIPASS', Path(sys.executable).parent))
    try:
        ensure_resources(root)
    except Exception as error:
        message = 'AnClicker 资源准备失败，请保留完整程序目录后重试。\n' + str(error)
        try:
            (root / 'resource-startup-error.log').write_text(message, encoding='utf-8')
        except OSError:
            pass
        if sys.platform == 'win32':
            import ctypes
            ctypes.windll.user32.MessageBoxW(None, message, 'AnClicker', 0x10)
        raise RuntimeError(message) from error
