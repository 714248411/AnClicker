"""Portable Data archives. All preparation happens outside the live directory."""
import contextlib
import hashlib
from functools import lru_cache
import json
import ntpath
import os
from pathlib import Path, PurePosixPath
import shutil
import sqlite3
import tempfile
import uuid
import zipfile
from anclicker.storage.project_paths import (INPUT_KEYS, input_keys, output_keys, literal_path,
    path_lines, resolve_parameters, relative_parameters, resolve_path, map_workbook_resources,
    background_paths, declared_outputs)

MANIFEST = 'portable-directories.json'

def directory_path(value, root, mappings):
    if not isinstance(value, str):
        return value
    normalized = value.replace('\\', '/').rstrip('/')
    for old, relative in sorted(mappings.items(), key=lambda item: -len(item[0])):
        old = old.replace('\\', '/').rstrip('/')
        if normalized.casefold() == old.casefold() or normalized.casefold().startswith(old.casefold() + '/'):
            suffix = normalized[len(old):].lstrip('/')
            candidate = Path(root) / relative / suffix
            try:
                candidate.resolve().relative_to(Path(root).resolve())
            except ValueError:
                continue
            if candidate.exists():
                return str(candidate)
    return value

def load_mappings(root):
    path = Path(root) / MANIFEST
    if not path.is_file():
        return {}
    data = _read_manifest(str(path), path.stat().st_mtime_ns, path.stat().st_size)
    mappings = data.get('directories', {})
    if data.get('format') != 1 or not isinstance(mappings, dict):
        raise ValueError('整体数据目录清单格式不正确')
    for old, relative in mappings.items():
        if not isinstance(old, str) or not isinstance(relative, str):
            raise ValueError('整体数据目录清单格式不正确')
        target = (Path(root) / relative).resolve()
        if not target.is_relative_to(Path(root).resolve()):
            raise ValueError('整体数据目录越界')
    return dict(mappings)

@lru_cache(maxsize=16)
def _read_manifest(path, modified, size):
    return json.loads(Path(path).read_text(encoding='utf-8'))

def _snapshot(source, target, database_path=None):
    source, target = Path(source), Path(target)
    target.mkdir(parents=True, exist_ok=True)
    for path in source.rglob('*'):
        if path.is_symlink() or (hasattr(path, 'is_junction') and path.is_junction()):
            raise ValueError(f'数据包含目录链接，请先复制实际文件：{path}')
        relative = path.relative_to(source)
        if path.is_dir():
            (target / relative).mkdir(parents=True, exist_ok=True)
        if path.is_file() and path.name not in ('命令集.db', '命令集.db-wal', '命令集.db-shm', '命令集.db-journal'):
            destination = target / relative
            destination.parent.mkdir(parents=True, exist_ok=True)
            shutil.copy2(path, destination)
    database_path = Path(database_path) if database_path else source / '命令集.db'
    if not database_path.is_file():
        from anclicker.storage.database import DatabaseOperation
        DatabaseOperation(str(target / '命令集.db'))
        return
    with contextlib.closing(sqlite3.connect(str(database_path))) as original:
        with contextlib.closing(sqlite3.connect(str(target / '命令集.db'))) as copied:
            original.backup(copied)


def absolute_inputs(parameters, command_type, base, root, resource_root=None):
    result = dict(parameters)
    for key in input_keys(command_type):
        value = result.get(key)
        if not isinstance(value, str) or '{{' in value or '☾' in value:
            continue
        lines = []
        for line in value.splitlines():
            if line and not ntpath.isabs(line):
                candidate = Path(base) / line
                if not candidate.exists():
                    candidate = Path(root) / line
                if not candidate.exists() and resource_root is not None:
                    candidate = Path(resource_root) / line
                if candidate.exists():
                    line = str(candidate.resolve())
            lines.append(line)
        result[key] = '\n'.join(lines)
    return result

def _inputs(parameters, command_type="", generated=None):
    if isinstance(parameters, dict):
        for key in input_keys(command_type):
            value = parameters.get(key)
            if literal_path(value):
                yield from (line for line in path_lines(value, command_type) if line.strip()
                            and (generated is None or ntpath.normcase(ntpath.normpath(line)) not in generated))
        nested, fields = background_paths(parameters, command_type)
        for key, output in fields.items():
            if not output and literal_path(nested[key]):
                delimiter = '|' if key in ('pic_name', 'pic') else '\n'
                yield from (line for line in nested[key].split(delimiter) if line.strip()
                            and (generated is None or ntpath.normcase(ntpath.normpath(line)) not in generated))
        if generated is not None:
            for value in declared_outputs(parameters, command_type):
                generated.add(ntpath.normcase(ntpath.normpath(value)))

def _database_inputs(path):
    with contextlib.closing(sqlite3.connect(str(path))) as conn:
        tables = {row[0] for row in conn.execute("SELECT name FROM sqlite_master WHERE type='table'")}
        if '命令' in tables:
            generated = set()
            for command_type, value in conn.execute('SELECT 类型标识, 参数JSON FROM 命令 ORDER BY 排序, ID'):
                yield from _inputs(json.loads(value), command_type, generated)
        if '变量池' in tables:
            from anclicker.storage.portable_migration import relocated_path
            for value, in conn.execute('SELECT 值 FROM 变量池'):
                if isinstance(value, str) and ntpath.isabs(value) and (Path(value).exists() or Path(relocated_path(value, path.parent)).exists()):
                    yield value
        if '最近打开' in tables:
            yield from (row[0] for row in conn.execute('SELECT 文件路径 FROM 最近打开') if row[0] and Path(row[0]).is_file())
        if '设置' in tables:
            settings = dict(conn.execute('SELECT 设置项, 值 FROM 设置'))
            current = settings.get('当前文件路径')
            if current and current != 'None':
                yield current
            for task in json.loads(settings.get('定时运行任务') or '[]'):
                for key in ('path', 'file_path', 'project_path'):
                    if task.get(key):
                        yield task[key]

def _workbook_inputs(path, source_root=None, original_path=None, *, project_only=False, resource_root=None):
    import openpyxl
    book = openpyxl.load_workbook(path, read_only=source_root is None, data_only=False, keep_vba=path.suffix.lower() == '.xlsm')
    try:
        if '命令' in book and '参数JSON' in [cell.value for cell in book['命令'][1]]:
            from anclicker.storage.graph_repository import GraphRepository
            GraphRepository(':memory:').validate_workbook(book)
            generated = set()
            for row in book['命令'].iter_rows(min_row=2):
                if row[0].value is not None:
                    parameters = json.loads(row[2].value)
                    if source_root is not None:
                        parameters = resolve_parameters(parameters, row[1].value, source_root, base=original_path.parent, fallback=resource_root)
                        row[2].value = json.dumps(parameters, ensure_ascii=False)
                    yield from _inputs(parameters, row[1].value, generated)
            if source_root is not None:
                if project_only:
                    from anclicker.storage.settings_defaults import PROJECT_SETTING_ITEMS
                    sheet = book['设置']
                    for index in range(sheet.max_row, 1, -1):
                        category, name = sheet.cell(index, 1).value, sheet.cell(index, 2).value
                        if category == '窗口大小' or (category == '设置' and name not in PROJECT_SETTING_ITEMS):
                            sheet.delete_rows(index)
                book.save(path)
        else:
            # Legacy projects are kept intact; collect explicit legacy image cells.
            for sheet in book:
                headers = [cell.value for cell in sheet[1]]
                if '图像名称' in headers and '指令类型' in headers:
                    index = headers.index('图像名称')
                    for row in sheet.iter_rows(min_row=2, values_only=True):
                        if len(row) > index and isinstance(row[index], str) and row[index]:
                            yield row[index]
    finally:
        book.close()

def export_data(folder, archive, *, project_only=False, database_path=None, resource_root=None):
    source, archive = Path(folder).resolve(), Path(archive).resolve()
    if archive.is_relative_to(source):
        raise ValueError('请将整体数据包保存到 Data 文件夹之外，避免递归打包。')
    if not project_only and not (source / '命令集.db').is_file():
        raise ValueError('Data 中没有命令集.db')
    with tempfile.TemporaryDirectory(prefix='anclicker-export-') as temporary:
        staged = Path(temporary) / 'Data'
        _snapshot(source, staged, database_path)
        if project_only:
            from anclicker.storage.settings_defaults import PROJECT_SETTING_ITEMS, PROJECT_SETTING_DEFAULTS
            from anclicker.storage.graph_repository import GraphRepository
            with contextlib.closing(sqlite3.connect(str(staged / '命令集.db'))) as conn:
                current = conn.execute("SELECT 值 FROM 设置 WHERE 设置项='当前文件路径'").fetchone()
                foreign = bool(current and current[0] and current[0] != 'None' and not Path(current[0]).resolve().is_relative_to(source))
                if foreign and database_path is None:
                    GraphRepository(str(staged / '命令集.db')).clear()
                with conn:
                    for name, in list(conn.execute('SELECT 设置项 FROM 设置')):
                        if name not in PROJECT_SETTING_ITEMS and name != '当前文件路径':
                            conn.execute('DELETE FROM 设置 WHERE 设置项=?', (name,))
                    conn.execute('DELETE FROM 窗口大小')
                    for path, in list(conn.execute('SELECT 文件路径 FROM 最近打开')):
                        if not Path(path).resolve().is_relative_to(source):
                            conn.execute('DELETE FROM 最近打开 WHERE 文件路径=?', (path,))
                    if foreign and database_path is None:
                        conn.execute("DELETE FROM 设置 WHERE 设置项='当前文件路径'")
                        conn.execute('DELETE FROM 资源文件夹')
                        conn.execute('DELETE FROM 变量池')
                        conn.executemany('UPDATE 设置 SET 值=? WHERE 设置项=?', [(value, key) for key, value in PROJECT_SETTING_DEFAULTS.items()])
        with contextlib.closing(sqlite3.connect(str(staged / '命令集.db'))) as conn:
            rows = list(conn.execute('SELECT ID, 类型标识, 参数JSON FROM 命令'))
            current = conn.execute("SELECT 值 FROM 设置 WHERE 设置项='当前文件路径'").fetchone()
            project_base = Path(current[0]).parent if current and current[0] and current[0] != 'None' else source
            with conn:
                for command_id, command_type, value in rows:
                    parameters = resolve_parameters(json.loads(value), command_type, source, base=project_base, fallback=resource_root)
                    conn.execute('UPDATE 命令 SET 参数JSON=? WHERE ID=?', (json.dumps(parameters, ensure_ascii=False), command_id))
                if database_path and Path(database_path).resolve().parent != source:
                    # Relative resource folders in the live database use its Data directory.
                    for path, in list(conn.execute('SELECT 路径 FROM 资源文件夹')):
                        if not ntpath.isabs(path):
                            absolute = str(Path(database_path).resolve().parent / path)
                            conn.execute('UPDATE OR IGNORE 资源文件夹 SET 路径=? WHERE 路径=?', (absolute, path))
        mappings = load_mappings(staged)
        mappings[str(source)] = '.'
        pending = [(value, source) for value in _database_inputs(staged / '命令集.db')]
        # Explicit resource directories are transferred as directories, including
        # files addressed through variables rather than literal command inputs.
        with contextlib.closing(sqlite3.connect(str(staged / '命令集.db'))) as conn:
            has_resources = conn.execute("SELECT 1 FROM sqlite_master WHERE name='资源文件夹'").fetchone()
            resources = list(conn.execute('SELECT 路径 FROM 资源文件夹')) if has_resources else []
        for value, in resources:
            resource = Path(value) if ntpath.isabs(value) else source / value
            default_images = {source / 'images'}
            if database_path:
                default_images.add(Path(database_path).resolve().parent / 'images')
            if not resource.is_dir() and resource in default_images:
                relative = 'images' if resource == source / 'images' else 'resources/' + hashlib.sha256(str(resource).encode('utf-8')).hexdigest()[:16]
                mappings[str(resource)] = relative
                (staged / relative).mkdir(parents=True, exist_ok=True)
                continue
            if not resource.is_dir():
                raise ValueError(f'资源目录不存在：{value}')
            resource = resource.resolve()
            if resource.is_relative_to(source):
                continue
            relative = 'resources/' + hashlib.sha256(str(resource).encode('utf-8')).hexdigest()[:16]
            mappings[str(resource)] = relative
            (staged / relative).mkdir(parents=True, exist_ok=True)
            for file in resource.rglob('*'):
                if file.is_symlink() or (hasattr(file, 'is_junction') and file.is_junction()):
                    raise ValueError(f'资源目录包含链接：{file}')
                if file.is_file():
                    destination = staged / relative / file.relative_to(resource)
                    destination.parent.mkdir(parents=True, exist_ok=True)
                    shutil.copy2(file, destination)
        def original_file(path):
            relative = path.relative_to(staged)
            original = source / relative
            if original.exists():
                return original
            for old, mapped in sorted(mappings.items(), key=lambda item: -len(item[1])):
                mapped = Path(mapped)
                if relative.is_relative_to(mapped):
                    candidate = Path(old) / relative.relative_to(mapped)
                    if candidate.exists():
                        return candidate
            return original
        books = [(p, original_file(p)) for p in staged.rglob('*')
                 if p.suffix.lower() in ('.xlsx', '.xlsm') and not p.name.startswith('~$')
                 and 'migration_backups' not in p.parts]
        visited = set()
        missing = set()
        while books or pending:
            while books:
                local, original = books.pop()
                if str(local) in visited:
                    continue
                visited.add(str(local))
                pending.extend((value, original.parent) for value in _workbook_inputs(local, source, original, project_only=project_only, resource_root=resource_root))
            if not pending:
                break
            value, base = pending.pop()
            candidate = Path(value) if ntpath.isabs(value) else base / value
            if not candidate.exists() and not ntpath.isabs(value):
                candidate = source / value
            if not candidate.exists():
                from anclicker.storage.portable_migration import relocated_path
                candidate = Path(relocated_path(value, source))
            if candidate.is_dir():
                resource = candidate.resolve()
                if not resource.is_relative_to(source):
                    relative = 'resources/' + hashlib.sha256(str(resource).encode('utf-8')).hexdigest()[:16]
                    mappings[str(resource)] = relative
                    (staged / relative).mkdir(parents=True, exist_ok=True)
                    for file in resource.rglob('*'):
                        if file.is_symlink() or (hasattr(file, 'is_junction') and file.is_junction()):
                            raise ValueError(f'资源目录包含链接：{file}')
                        if file.is_file():
                            target = staged / relative / file.relative_to(resource)
                            target.parent.mkdir(parents=True, exist_ok=True)
                            shutil.copy2(file, target)
                            if target.suffix.lower() in ('.xlsx', '.xlsm'):
                                books.append((target, file))
                continue
            if not candidate.is_file():
                missing.add(value)
                continue
            candidate = candidate.resolve()
            if candidate.is_relative_to(source):
                continue
            parent = str(candidate.parent)
            relative = mappings.get(parent)
            if relative is None:
                relative = 'resources/' + hashlib.sha256(parent.encode('utf-8')).hexdigest()[:16]
                mappings[parent] = relative
            target = staged / relative / candidate.name
            if not target.exists():
                target.parent.mkdir(parents=True, exist_ok=True)
                shutil.copy2(candidate, target)
                if target.suffix.lower() in ('.xlsx', '.xlsm'):
                    books.append((target, candidate))
        if missing:
            raise ValueError('以下引用文件缺失，未生成不完整的数据包：\n' + '\n'.join(sorted(missing)))
        if project_only:
            _make_project_paths_relative(staged, mappings)
        (staged / MANIFEST).write_text(json.dumps({'format': 1, 'directories': mappings}, ensure_ascii=False, indent=2), encoding='utf-8')
        if project_only:
            (staged / 'project-export.json').write_text(json.dumps({'format': 2, 'name': source.name, 'paths': 'page-relative'}), encoding='utf-8')
        archive.parent.mkdir(parents=True, exist_ok=True)
        temporary_zip = archive.with_name(archive.name + '.' + uuid.uuid4().hex + '.tmp')
        try:
            with zipfile.ZipFile(temporary_zip, 'w', zipfile.ZIP_DEFLATED, allowZip64=True) as out:
                for path in staged.rglob('*'):
                    if path.is_file() or path.is_dir():
                        out.write(path, 'Data/' + path.relative_to(staged).as_posix())
            with zipfile.ZipFile(temporary_zip) as check:
                if check.testzip():
                    raise ValueError('导出压缩包校验失败')
            os.replace(temporary_zip, archive)
        finally:
            temporary_zip.unlink(missing_ok=True)
    return archive


def _make_project_paths_relative(data, mappings):
    """Only operate on the export snapshot, after all dependencies are collected."""
    import openpyxl
    from anclicker.storage.project_paths import mapped_path
    with contextlib.closing(sqlite3.connect(str(data / '命令集.db'))) as conn, conn:
        row = conn.execute("SELECT 值 FROM 设置 WHERE 设置项='当前文件路径'").fetchone()
        current = mapped_path(row[0], data, mappings=mappings) if row and row[0] else ''
        base = Path(current).parent if current and current != 'None' else data
        # Register generated output mappings before rebasing any downstream reads.
        rows = list(conn.execute('SELECT ID, 类型标识, 参数JSON FROM 命令 ORDER BY 排序, ID'))
        for _, kind, value in rows:
            relative_parameters(json.loads(value), kind, data, base, mappings=mappings, external_outputs=True)
        for command_id, kind, value in rows:
            values = relative_parameters(json.loads(value), kind, data, base, mappings=mappings, external_outputs=True)
            conn.execute('UPDATE 命令 SET 参数JSON=? WHERE ID=?', (json.dumps(values, ensure_ascii=False), command_id))
    for path in data.rglob('*'):
        if path.suffix.lower() not in ('.xlsx', '.xlsm') or path.name.startswith('~$') or 'migration_backups' in path.parts:
            continue
        book = openpyxl.load_workbook(path, keep_vba=path.suffix.lower() == '.xlsm')
        try:
            if {'命令', '节点', '连线', '设置'} <= set(book.sheetnames):
                rows = [row for row in book['命令'].iter_rows(min_row=2) if row[0].value is not None]
                for row in rows:
                    relative_parameters(json.loads(row[2].value), row[1].value, data, path.parent,
                                        mappings=mappings, external_outputs=True)
                for row in rows:
                    values = relative_parameters(json.loads(row[2].value), row[1].value, data, path.parent,
                                                 mappings=mappings, external_outputs=True)
                    row[2].value = json.dumps(values, ensure_ascii=False)
                map_workbook_resources(book, lambda value: relative_parameters(
                    {'folder': value}, '', data, path.parent, mappings=mappings)['folder'])
                book.save(path)
        finally:
            book.close()

def prepare_import(archive, parent, *, validate_resources=True, prefix='Data'):
    stage = Path(tempfile.mkdtemp(prefix='.anclicker-import-', dir=parent))
    try:
        seen = set()
        with zipfile.ZipFile(archive) as package:
            if sum(item.file_size for item in package.infolist()) > shutil.disk_usage(parent).free:
                raise ValueError('磁盘空间不足，无法完整导入数据包')
            for item in package.infolist():
                name = item.filename.replace('\\', '/')
                path = PurePosixPath(name)
                if any(part.endswith((' ', '.')) or (getattr(ntpath, 'isreserved', lambda text: text.split('.')[0].upper() in {'CON','PRN','AUX','NUL'})(part)) for part in path.parts):
                    raise ValueError('数据包包含无效的 Windows 文件名')
                if path.is_absolute() or '..' in path.parts or not path.parts or (prefix is not None and path.parts[0] != prefix) or ':' in name:
                    raise ValueError('数据包包含不安全路径')
                if (item.external_attr >> 16) & 0o170000 == 0o120000:
                    raise ValueError('数据包不能包含符号链接')
                key = name.rstrip('/').casefold()
                if key in seen:
                    raise ValueError('数据包包含重名文件')
                seen.add(key)
                destination = stage.joinpath(*path.parts)
                if item.is_dir():
                    destination.mkdir(parents=True, exist_ok=True)
                else:
                    destination.parent.mkdir(parents=True, exist_ok=True)
                    with package.open(item) as incoming, destination.open('wb') as output:
                        shutil.copyfileobj(incoming, output)
        if prefix is None:
            return stage
        validate_import_data(stage / 'Data', validate_resources=validate_resources)
        return stage
    except Exception:
        shutil.rmtree(stage)
        raise


def validate_import_data(data, *, validate_resources=True):
    data = Path(data)
    db = data / '命令集.db'
    if not db.is_file():
        raise ValueError('数据包缺少 Data/命令集.db')
    with contextlib.closing(sqlite3.connect(str(db))) as conn:
        if conn.execute('PRAGMA integrity_check').fetchone()[0] != 'ok':
            raise ValueError('数据包的数据库校验失败')
        tables = {row[0] for row in conn.execute("SELECT name FROM sqlite_master WHERE type='table'")}
        if not {'命令', '节点', '节点连接', '设置'} <= tables:
            raise ValueError('整体导入需要新版 Data 数据库；旧版项目请先通过导入指令完成迁移。')
    load_mappings(data)
    from anclicker.storage.graph_repository import GraphRepository
    from anclicker.storage.portable_migration import relocated_path
    with contextlib.closing(sqlite3.connect(str(db))) as conn:
        GraphRepository._validate_draft_connection(conn)
    with contextlib.closing(sqlite3.connect(str(db))) as conn:
        current = conn.execute("SELECT 值 FROM 设置 WHERE 设置项='当前文件路径'").fetchone()
    base = Path(relocated_path(current[0], data)).parent if current and current[0] and current[0] != 'None' else data
    inputs = [(v, base) for v in _database_inputs(db)]
    for path in data.rglob('*'):
        if path.suffix.lower() in ('.xlsx', '.xlsm') and not path.name.startswith('~$') and 'migration_backups' not in path.parts:
            inputs.extend((v, path.parent) for v in _workbook_inputs(path))
    missing = []
    for value, base in inputs:
        mapped = relocated_path(value, data)
        candidate = Path(mapped) if ntpath.isabs(mapped) else base / mapped
        if not candidate.exists() and not ntpath.isabs(mapped):
            candidate = data / mapped
        if not candidate.exists() or not candidate.resolve().is_relative_to(data.resolve()):
            missing.append(value)
    if missing and validate_resources:
        raise ValueError('数据包缺少引用文件，未替换当前 Data：\n' + '\n'.join(sorted(set(missing))))

def apply_import(stage, folder, *, adapt=True, remember=False, new_partition=False, disable_schedules=True):
    """Called after the GUI event loop closes, before restarting the application."""
    stage, folder = Path(stage), Path(folder)
    backup = folder.with_name(folder.name + '-导入前备份-' + uuid.uuid4().hex[:12])
    existed = folder.exists()
    if existed and new_partition:
        raise FileExistsError('分区目录已被占用，请重新导入选择下一编号。')
    if existed:
        folder.rename(backup)
    try:
        (stage / 'Data').rename(folder)
        from anclicker.storage.portable_migration import relocate_database
        relocate_database(folder / '命令集.db', folder, repair_commands=adapt)
        if adapt:
            relocate_project_files(folder, force=True)
        if new_partition and disable_schedules:
            # Loading someone else's program must not execute their schedules.
            with contextlib.closing(sqlite3.connect(str(folder / '命令集.db'))) as conn:
                row = conn.execute('SELECT 值 FROM 设置 WHERE 设置项=?', ('定时运行任务',)).fetchone()
                if row and row[0]:
                    tasks = json.loads(row[0])
                    for task in tasks:
                        task.update(enabled=False, status='未启用')
                    with conn:
                        conn.execute('UPDATE 设置 SET 值=? WHERE 设置项=?', (json.dumps(tasks, ensure_ascii=False), '定时运行任务'))
        register_imported_projects(folder)
        if remember:
            from anclicker.storage.data_partitions import select_partition
            select_partition(folder)
    except Exception:
        if folder.exists():
            folder.rename(stage / 'Data')
        if existed:
            backup.rename(folder)
        raise
    stage.rmdir()
    return backup if existed else None


def relocate_project_files(folder, *, force=False):
    """Batch-repair saved projects once per Data location, without editing graph rows."""
    import openpyxl
    from anclicker.storage.portable_migration import relocated_path, relocate_command_files
    folder = Path(folder).resolve()
    marker = folder / '.portable-location.json'
    if not force and marker.is_file() and json.loads(marker.read_text(encoding='utf-8')).get('root') == str(folder):
        return 0
    mappings = load_mappings(folder)
    mappings[str(folder)] = '.'
    (folder / MANIFEST).write_text(json.dumps({'format': 1, 'directories': mappings}, ensure_ascii=False, indent=2), encoding='utf-8')
    count = 0
    for path in list(folder.rglob('*')):
        if path.suffix.lower() not in ('.xlsx', '.xlsm') or path.name.startswith('~$') or 'migration_backups' in path.parts:
            continue
        try:
            book = openpyxl.load_workbook(path, keep_vba=path.suffix.lower() == '.xlsm')
        except (zipfile.BadZipFile, OSError):
            continue
        changed = False
        try:
            if {'命令', '节点', '连线', '设置'} <= set(book.sheetnames):
                for row in book['命令'].iter_rows(min_row=2):
                    if row[0].value is None:
                        continue
                    value = json.loads(row[2].value)
                    new = relocate_command_files(value, folder, command_type=row[1].value, project_path=path)
                    if new != value:
                        row[2].value = json.dumps(new, ensure_ascii=False)
                        changed = True
                changed |= map_workbook_resources(book, lambda value: resolve_path(value, folder, base=path.parent))
            if changed:
                backup = folder / 'migration_backups' / 'projects' / path.relative_to(folder)
                backup.parent.mkdir(parents=True, exist_ok=True)
                if not backup.exists():
                    shutil.copy2(path, backup)
                temporary = path.with_name(path.stem + '.relocating' + path.suffix)
                try:
                    book.save(temporary)
                    os.replace(temporary, path)
                finally:
                    temporary.unlink(missing_ok=True)
                count += 1
        finally:
            book.close()
    marker.write_text(json.dumps({'root': str(folder)}, ensure_ascii=False), encoding='utf-8')
    return count


def register_imported_projects(folder):
    """Rebuild the imported partition's recent list from its runnable workbooks."""
    import openpyxl
    from anclicker.storage.graph_repository import GraphRepository
    from anclicker.storage.data_partitions import bounded_entries
    from anclicker.storage.recent_projects import RecentProjectsRepository
    folder = Path(folder).resolve()
    projects = []
    for path in bounded_entries(folder):
        path = Path(path)
        if not path.is_file() or path.suffix.lower() not in ('.xlsx', '.xlsm') or path.name.startswith('~$'):
            continue
        book = None
        try:
            book = openpyxl.load_workbook(path, read_only=True)
            if {'命令', '节点', '连线', '设置'} <= set(book.sheetnames):
                GraphRepository(':memory:').validate_workbook(book)
                runnable = True
            else:
                runnable = any({'指令类型', '图像名称'} <= {cell.value for cell in sheet[1]} for sheet in book)
            if runnable:
                projects.append(str(path))
        except (ValueError, KeyError, IndexError, TypeError, OSError, zipfile.BadZipFile):
            continue
        finally:
            if book is not None:
                book.close()
    projects.sort(key=lambda p: str(Path(p).relative_to(folder)).casefold())
    db = folder / '命令集.db'
    with contextlib.closing(sqlite3.connect(str(db))) as conn:
        with conn:
            conn.execute('DELETE FROM 最近打开')
            from anclicker.storage.settings_defaults import get_setting_type
            conn.execute('INSERT OR REPLACE INTO 设置(类型, 设置项, 值) VALUES (?, ?, ?)',
                         (get_setting_type('项目最近文件全部保留'), '项目最近文件全部保留', 'True'))
    RecentProjectsRepository(str(db)).add_recent_files(projects)
    return projects
