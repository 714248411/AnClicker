"""Relocate copied portable project references without touching command payloads."""
import contextlib
import json
import ntpath
import os
import sqlite3
from pathlib import Path


def copied_data_folder(folder):
    """Accept a whole Data folder pasted into an otherwise empty Data folder."""
    root = Path(folder)
    if not (root / '命令集.db').is_file():
        nested = root / 'Data'
        if (nested / '命令集.db').is_file():
            return str(nested)
    return str(root)


def relocated_path(value, folder):
    if not isinstance(value, str) or not value or '\n' in value:
        return value
    from anclicker.storage.data_bundle import directory_path, load_mappings
    mapped = directory_path(value, folder, load_mappings(folder))
    if mapped != value:
        return mapped
    # Only exact Data-relative counterparts; never guess by basename.
    parts = value.replace('\\', '/').split('/')
    if not (ntpath.isabs(value) or value.startswith('/')):
        return value
    candidates = []
    for index, part in enumerate(parts):
        from anclicker.storage.project_paths import PARTITION
        if not PARTITION.fullmatch(part):
            continue
        tail = parts[index + 1:]
        if any(p in ('.', '..') for p in tail):
            continue
        target = Path(folder).joinpath(*tail)
        try:
            target.resolve().relative_to(Path(folder).resolve())
        except ValueError:
            continue
        if target.exists() and target not in candidates:
            candidates.append(target)
    return str(candidates[0]) if len(candidates) == 1 else value


def relocate_command_files(parameters, folder, *, strict=True, include_images=True, command_type="", project_path=None):
    """Resolve declared path fields; code, URLs, prose and variable expressions stay intact."""
    from anclicker.storage.project_paths import resolve_parameters
    result = resolve_parameters(parameters, command_type, folder,
                                base=Path(project_path).parent if project_path else folder)
    if not include_images:
        for key in ('图像路径', '图像', '图片'):
            if key in parameters:
                result[key] = parameters[key]
    return result


def relocate_database(db_path, folder, *, repair_commands=True):
    """Repair project/settings references transactionally, with a SQLite backup."""
    if not Path(db_path).is_file():
        return 0
    updates = []
    with contextlib.closing(sqlite3.connect(db_path)) as conn:
        tables = {r[0] for r in conn.execute("SELECT name FROM sqlite_master WHERE type='table'")}
        for table, column in (('最近打开', '文件路径'), ('资源文件夹', '路径')):
            if table not in tables:
                continue
            occupied = {r[0] for r in conn.execute('SELECT 路径 FROM 资源文件夹')} if table == '资源文件夹' else set()
            for rowid, value in conn.execute(f'SELECT rowid, "{column}" FROM "{table}"'):
                target = relocated_path(value, folder)
                if target != value:
                    # Resource folder paths are unique. Preserve an existing row.
                    if table == '资源文件夹' and target in occupied:
                        continue
                    occupied.add(target)
                    updates.append((f'UPDATE "{table}" SET "{column}"=? WHERE rowid=?', (target, rowid)))
        if repair_commands and '命令' in tables:
            current = conn.execute("SELECT 值 FROM 设置 WHERE 设置项='当前文件路径'").fetchone() if '设置' in tables else None
            project_path = relocated_path(current[0], folder) if current and current[0] and current[0] != 'None' else None
            columns = {r[1] for r in conn.execute('PRAGMA table_info(命令)')}
            if {'ID', '参数JSON'} <= columns:
                for command_id, command_type, value in conn.execute('SELECT ID, 类型标识, 参数JSON FROM 命令'):
                    try:
                        parameters = json.loads(value)
                    except (ValueError, TypeError):
                        continue
                    if not isinstance(parameters, dict):
                        continue
                    changed = relocate_command_files(parameters, folder, strict=False, command_type=command_type, project_path=project_path)
                    if changed != parameters:
                        updates.append(('UPDATE 命令 SET 参数JSON=? WHERE ID=?',
                                        (json.dumps(changed, ensure_ascii=False), command_id)))
        if repair_commands and '变量池' in tables:
            for name, value in conn.execute('SELECT 变量名称, 值 FROM 变量池'):
                target = relocated_path(value, folder)
                if target != value:
                    updates.append(('UPDATE 变量池 SET 值=? WHERE 变量名称=?', (target, name)))
        if '设置' in tables:
            for name, value in conn.execute('SELECT 设置项, 值 FROM 设置'):
                target = value
                if name in ('当前文件路径', '本机新建默认保存路径'):
                    target = relocated_path(value, folder)
                elif name in ('本机项目控制设置', '本机项目已保存内容'):
                    try:
                        mapping = json.loads(value)
                        if isinstance(mapping, dict):
                            if name == '本机项目已保存内容':
                                changed = dict(mapping)
                                if mapping.get('path'):
                                    changed['path'] = os.path.normcase(relocated_path(mapping['path'], folder))
                            else:
                                changed = {os.path.normcase(relocated_path(k, folder)): v for k, v in mapping.items()}
                            if len(changed) == len(mapping) and changed != mapping:
                                target = json.dumps(changed, ensure_ascii=False)
                    except (ValueError, TypeError):
                        pass
                elif name == '定时运行任务':
                    try:
                        tasks = json.loads(value)
                        if isinstance(tasks, list):
                            changed = False
                            for task in tasks:
                                if isinstance(task, dict):
                                    for key in ('path', 'file_path', 'project_path'):
                                        if key in task:
                                            new_path = relocated_path(task[key], folder)
                                            changed |= new_path != task[key]
                                            task[key] = new_path
                            if changed:
                                target = json.dumps(tasks, ensure_ascii=False)
                    except (ValueError, TypeError):
                        pass
                if target != value:
                    updates.append(('UPDATE 设置 SET 值=? WHERE 设置项=?', (target, name)))
        if not updates:
            return 0
        backup_dir = Path(folder) / 'migration_backups'
        backup_dir.mkdir(parents=True, exist_ok=True)
        import uuid
        backup = backup_dir / ('迁移前-' + uuid.uuid4().hex + '.db')
        with contextlib.closing(sqlite3.connect(str(backup))) as destination:
            conn.backup(destination)
        with conn:
            for sql, parameters in updates:
                conn.execute(sql, parameters)
    return len(updates)
