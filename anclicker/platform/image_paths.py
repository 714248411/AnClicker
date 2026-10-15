"""Portable image references rooted at the writable application data directory."""
from contextlib import contextmanager
from contextvars import ContextVar
import hashlib
import json
import ntpath
import os
from pathlib import Path
import re
import shutil

from anclicker.app.paths import DATA_FOLDER

_VARIABLE = re.compile(r'\{\{.*?\}\}|☾.*?☽')
_IMPORTS = ContextVar('image_imports', default=None)
IMAGE_KEYS = ('图像路径', '图像', '图片')


def _root(data_folder=None):
    return Path(data_folder or DATA_FOLDER).resolve()


def _parts(value):
    return str(value).replace('\\', '/').split('/')


def resolve_image_reference(value, *, project_path=None, resource_folders=(),
                            data_folder=None, legacy_search=True):
    """Resolve data-relative paths first; read legacy files without modifying them.

    Structured relative references never fall back to a different basename.
    Old absolute paths may be relocated by their suffix below ``data``. Only
    legacy bare names/absolute references use catalog search, requiring uniqueness.
    """
    text = str(value or '')
    if not text or _VARIABLE.search(text):
        return text
    root = _root(data_folder)
    path = Path(os.path.expanduser(text.replace('\\', '/')))
    absolute = path.is_absolute() or ntpath.isabs(text)
    if absolute and path.is_file():
        return str(path.resolve())
    parts = _parts(text)
    if absolute:
        for index in reversed(range(len(parts))):
            if parts[index].casefold() == 'data':
                candidate = root.joinpath(*parts[index + 1:]).resolve()
                if candidate.is_relative_to(root) and candidate.is_file():
                    return str(candidate)
                break
    else:
        candidate = (root / path).resolve()
        if candidate.is_relative_to(root) and candidate.is_file():
            return str(candidate)
        if project_path:
            project_folder = Path(project_path).expanduser().resolve().parent
            for legacy in (project_folder / path, project_folder / 'data' / path):
                if legacy.is_file():
                    return str(legacy.resolve())
        # A subdirectory is significant; don't silently pick another image.
        if len(parts) > 1 or not legacy_search:
            return str(candidate if candidate.is_relative_to(root) else root / '__invalid_image_path__')
    if legacy_search:
        name = ntpath.basename(text)
        matches = set()
        for folder in (root / 'images', *map(Path, resource_folders)):
            if folder.is_dir():
                matches.update(p.resolve() for p in folder.rglob('*') if p.is_file() and p.name == name)
        if len(matches) > 1:
            raise ValueError(f'图片名称重复，请重新选择明确的图片路径：{name}')
        if matches:
            return str(matches.pop())
    return str(path if absolute else root / path)


def _digest(path):
    result = hashlib.sha256()
    with path.open('rb') as stream:
        for block in iter(lambda: stream.read(1024 * 1024), b''):
            result.update(block)
    return result.hexdigest()


def store_image_reference(value, *, project_path=None, resource_folders=(), data_folder=None,
                          prefer_project=False):
    """Copy external inputs into data/images and return a POSIX relative path.

    Missing legacy references and runtime variables remain readable/editable.
    Existing images below data keep their complete subdirectory. Never move or
    overwrite a user's source image; same-name different bytes get a digest suffix.
    """
    text = str(value or '')
    if not text or _VARIABLE.search(text):
        return text
    root = _root(data_folder)
    if prefer_project and project_path and not ntpath.isabs(text):
        relative = Path(text.replace('\\', '/'))
        project_folder = Path(project_path).expanduser().resolve().parent
        for candidate in (project_folder / relative, project_folder / 'data' / relative):
            if candidate.is_file():
                text = str(candidate.resolve())
                break
    source = Path(resolve_image_reference(text, project_path=project_path,
                  resource_folders=resource_folders, data_folder=root))
    if not source.is_file():
        return text
    source = source.resolve()
    if source.is_relative_to(root):
        return source.relative_to(root).as_posix()
    folder = root / 'images'
    folder.mkdir(parents=True, exist_ok=True)
    folder = folder.resolve()
    if not folder.is_relative_to(root):
        raise ValueError('图片目录必须位于应用数据目录内')
    digest = _digest(source)
    target = folder / source.name
    while True:
        if target.exists():
            if target.is_file() and not target.is_symlink() and _digest(target) == digest:
                break
            target = folder / f'{source.stem}_{digest}{source.suffix}'
            if target.exists() and (not target.is_file() or target.is_symlink() or _digest(target) != digest):
                raise ValueError(f'图片目标文件冲突：{target.name}')
            continue
        try:
            output = target.open('xb')
        except FileExistsError:
            continue
        try:
            with output, source.open('rb') as stream:
                shutil.copyfileobj(stream, output)
        except BaseException:
            target.unlink(missing_ok=True)
            raise
        pending = _IMPORTS.get()
        if pending is not None:
            pending.append(target)
        break
    return target.relative_to(root).as_posix()


@contextmanager
def image_import_batch():
    """Roll back newly copied assets when workbook persistence fails."""
    parent = _IMPORTS.get()
    created = []
    token = _IMPORTS.set(created)
    try:
        yield
    except BaseException:
        for path in reversed(created):
            path.unlink(missing_ok=True)
        raise
    else:
        if parent is not None:
            parent.extend(created)
    finally:
        _IMPORTS.reset(token)


def map_background_images(method, values, transform):
    """Map only image inputs; capture outputs, dictionaries and colors are intact."""
    result = dict(values)
    method = method.casefold()
    if not (method.startswith('findpic') or method in {
            'ocrinfile', 'loadpic', 'freepic', 'getpicsize', 'imagetobmp',
            'createfoobarcustom', 'foobardrawpic'}):
        return result
    for key in ('pic_name', 'pic'):
        if isinstance(result.get(key), str):
            result[key] = '|'.join(transform(part) for part in result[key].split('|'))
    return result


def normalize_image_parameters(parameters, *, type_id='', project_path=None,
                               resource_folders=(), data_folder=None, prefer_project=False):
    result = dict(parameters)

    def store(value):
        return store_image_reference(value, project_path=project_path,
                 resource_folders=resource_folders, data_folder=data_folder,
                 prefer_project=prefer_project)

    for key in IMAGE_KEYS:
        if isinstance(result.get(key), str):
            text = result[key]
            if type_id == '多图点击':
                text = text.replace(';', '\n').replace('、', '\n')
            result[key] = '\n'.join(store(item) for item in text.split('\n'))
    if type_id.startswith('后台') and isinstance(result.get('参数'), str):
        values = json.loads(result['参数'])
        if isinstance(values, dict):
            method = str(result.get('接口', '')).strip().rsplit(' · ', 1)[-1]
            result['参数'] = json.dumps(map_background_images(method, values, store), ensure_ascii=False)
    return result
