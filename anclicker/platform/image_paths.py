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
from anclicker.app.installation_paths import get_install_folder, storage_install_folder

_VARIABLE = re.compile(r'\{\{.*?\}\}|☾.*?☽')
_IMPORTS = ContextVar('image_imports', default=None)
IMAGE_KEYS = ('图像路径', '图像', '图片')


def _root(data_folder=None):
    return Path(data_folder or DATA_FOLDER).resolve()


def _parts(value):
    return str(value).replace('\\', '/').split('/')


def resolve_image_reference(value, *, project_path=None, resource_folders=(),
                            data_folder=None, legacy_search=True, install_folder=None, allow_adaptation=True):
    """Prefer valid explicit absolute paths, then the portable Data directory.

    Missing references may be recovered by a unique filename anywhere in Data.
    Valid explicit paths always win; ambiguous filenames are never guessed.
    """
    text = str(value or '')
    if not text or _VARIABLE.search(text):
        return text
    root = _root(data_folder)
    path = Path(os.path.expanduser(text.replace('\\', '/')))
    absolute = path.is_absolute() or ntpath.isabs(text)
    if absolute and path.is_file():
        return str(path.resolve())
    if project_path:
        from anclicker.storage.data_partitions import original_reference, project_partition
        # Explicit project opens have already requested consent for missing paths.
        # Do not silently select a different partition during execution.
        preferred = project_partition(project_path, root.parent) or root
        original = original_reference(text, project_path, preferred)
        if original is not None and original.is_file():
            return str(original)
        if not allow_adaptation:
            return str(path if absolute else preferred / path)
    parts = _parts(text)
    install = storage_install_folder(Path(install_folder or get_install_folder()).resolve())
    relative = path if not absolute else None
    for index in reversed(range(len(parts))):
        if parts[index].casefold() in ('data',):
            relative = Path(*parts[index+1:])
            break
        if parts[index].casefold() == 'images':
            relative = Path(*parts[index:])
            break
    if relative is not None:
        for base in (install / 'Data',):
            candidate = (base / relative).resolve()
            if candidate.is_relative_to(base.resolve()) and candidate.is_file():
                return str(candidate)
    exact = (root / path).resolve() if not absolute else path
    if not absolute and exact.is_relative_to(root) and exact.is_file():
        return str(exact)
    if legacy_search:
        name = ntpath.basename(text)
        matches = set()
        for base in {install / 'Data', root}:
            if base.is_dir():
                matches.update(p.resolve() for p in base.rglob('*')
                               if p.is_file() and p.name.casefold() == name.casefold()
                               and p.resolve().is_relative_to(base.resolve()))
        if len(matches) > 1:
            raise ValueError(f'启动目录中图片名称重复，请选择明确的图片路径：{name}')
        if matches:
            return str(matches.pop())
    if absolute and path.is_file():
        return str(path.resolve())
    # Relocate both absolute and data-prefixed portable references.
    if absolute or (parts and parts[0].casefold() in ('data', '..', '.')):
        for index in reversed(range(len(parts))):
            if parts[index].casefold() in ('data',):
                candidate = root.joinpath(*parts[index + 1:]).resolve()
                if candidate.is_relative_to(root) and candidate.is_file():
                    return str(candidate)
                break
    if not absolute:
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
        direct = root / name
        if direct.is_file():
            return str(direct.resolve())
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


def repair_command_image_paths(command, context):
    """Repair static missing image inputs, persisting only this command's changes."""
    original = command.parameters
    repaired = dict(original)
    metadata = getattr(context, 'metadata', {})
    database = getattr(getattr(context, 'runtime', None), 'database', None) or metadata.get('database')
    project = metadata.get('project_path')
    for key in IMAGE_KEYS:
        value = original.get(key)
        if not isinstance(value, str) or not value or _VARIABLE.search(value):
            continue
        values = value.replace(';', '\n').replace('、', '\n') if command.type_id == '多图点击' else value
        resolved = []
        for item in values.split('\n'):
            direct = Path(item.replace('\\', '/'))
            if not direct.is_absolute() and not ntpath.isabs(item):
                direct = _root() / direct
            if direct.is_file():
                resolved.append(item)
                continue
            found = resolve_image_reference(item, project_path=project, allow_adaptation=False)
            if item and Path(found).is_file():
                resolved.append(found)
            else:
                resolved.append(item)
        repaired[key] = '\n'.join(resolved)
    if repaired == original:
        return False
    if database is not None and command.id is not None:
        from anclicker.storage.graph_repository import GraphRepository
        from anclicker.domain.instructions import InstructionDraft
        repository = GraphRepository(database.db_path, data_folder=_root())
        current = repository.get_command(command.id)
        if current is not None and current.parameters == original:
            saved = repository.update_command(command.id, InstructionDraft(command.type_id, repaired,
                command.repeat_count, command.error_policy, command.note))
            repaired = saved.parameters
    command.parameters = repaired
    return True
