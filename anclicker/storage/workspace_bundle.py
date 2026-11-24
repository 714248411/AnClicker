"""Project exports and a flat, versioned backup of every project and global setting."""
import contextlib
import json
import ntpath
import os
from pathlib import Path
import re
import shutil
import sqlite3
import tempfile
import uuid
import zipfile

from anclicker.storage.data_bundle import export_data, prepare_import, validate_import_data, apply_import
from anclicker.storage.data_partitions import PARTITION, select_partition
from anclicker.storage.project_catalog import available_projects, project_root, CURRENT_DIRECTORY, PROJECT_DIRECTORIES
from anclicker.storage.settings import LOCAL_PROJECT_SETTINGS, SettingsRepository
from anclicker.storage.settings_defaults import PROJECT_SETTING_ITEMS, get_setting_type

MANIFEST = 'anclicker-workspace.json'
SETTINGS = 'software-settings.json'
PLAN = '.restore-plan.json'


def current_project(db):
    return project_root(db, db.get_setting_value(CURRENT_DIRECTORY) or Path(db.db_path).parent)


def read_global_settings(db_path):
    with contextlib.closing(sqlite3.connect(str(db_path))) as conn:
        conn.execute('BEGIN')
        rows = [list(row) for row in conn.execute('SELECT 类型, 设置项, 值 FROM 设置')
                if row[1] not in PROJECT_SETTING_ITEMS | LOCAL_PROJECT_SETTINGS]
        windows = [list(row) for row in conn.execute('SELECT 窗口, 大小 FROM 窗口大小')]
    return {'settings': rows, 'windows': windows}


def validate_global_settings(settings):
    if not isinstance(settings, dict) or set(settings) != {'settings', 'windows'}:
        raise ValueError('整体数据包的软件设置格式无效')
    for key, width, name_column in (('settings', 3, 1), ('windows', 2, 0)):
        rows = settings[key]
        if not isinstance(rows, list):
            raise ValueError('整体数据包的软件设置格式无效')
        seen = set()
        for row in rows:
            if not isinstance(row, list) or len(row) != width or not all(isinstance(v, str) for v in row):
                raise ValueError('整体数据包的软件设置记录无效')
            name = row[name_column]
            if not name or name in seen:
                raise ValueError('整体数据包的软件设置重名')
            seen.add(name)
            if key == 'settings' and name in PROJECT_SETTING_ITEMS | LOCAL_PROJECT_SETTINGS:
                raise ValueError('整体数据包混入了项目参数')
            if key == 'windows' and SettingsRepository._parse_window_state(row[1]) is None:
                raise ValueError('整体数据包的窗口位置或大小无效')


def write_global_settings(db_path, settings):
    validate_global_settings(settings)
    with contextlib.closing(sqlite3.connect(str(db_path))) as conn, conn:
        for name, in list(conn.execute('SELECT 设置项 FROM 设置')):
            if name not in PROJECT_SETTING_ITEMS | LOCAL_PROJECT_SETTINGS:
                conn.execute('DELETE FROM 设置 WHERE 设置项=?', (name,))
        conn.executemany('INSERT OR REPLACE INTO 设置(类型, 设置项, 值) VALUES (?,?,?)', settings['settings'])
        conn.execute('DELETE FROM 窗口大小')
        conn.executemany('INSERT INTO 窗口大小(窗口, 大小) VALUES (?,?)', settings['windows'])


def configure_project(db_path, destination, catalog=None):
    settings = {CURRENT_DIRECTORY: str(destination), '最近导入项目文件夹': str(destination)}
    if catalog is not None:
        settings[PROJECT_DIRECTORIES] = json.dumps(list(map(str, catalog)), ensure_ascii=False)
    with contextlib.closing(sqlite3.connect(str(db_path))) as conn, conn:
        conn.executemany('INSERT OR REPLACE INTO 设置(类型, 设置项, 值) VALUES (?,?,?)',
                         [(get_setting_type(key), key, value) for key, value in settings.items()])


def export_project(db, folder, archive):
    folder = Path(folder).resolve()
    if folder not in available_projects(db):
        raise ValueError('项目目录不存在，请重新选择项目')
    return export_data(folder, archive, project_only=True,
                       database_path=db.db_path if folder == current_project(db) else None,
                       resource_root=Path(db.db_path).resolve().parent)


def export_workspace(db, archive):
    roots = available_projects(db)
    active = current_project(db)
    if active not in roots:
        raise ValueError('当前项目目录不可用，无法导出完整数据')
    archive = Path(archive).resolve()
    if any(archive.is_relative_to(root) for root in roots):
        raise ValueError('请将整体数据包保存在所有项目目录之外')
    settings = read_global_settings(db.db_path)
    validate_global_settings(settings)
    projects = [{'id': f'p{index}', 'name': root.name, 'source': str(root)} for index, root in enumerate(roots)]
    selected = Path(db.get_setting_value(CURRENT_DIRECTORY) or active).resolve()
    manifest = {'format': 1, 'kind': 'workspace', 'projects': projects,
                'active': projects[roots.index(active)]['id'], 'active_directory': selected.relative_to(active).as_posix()}
    archive.parent.mkdir(parents=True, exist_ok=True)
    output = archive.with_name(archive.name + '.' + uuid.uuid4().hex + '.tmp')
    try:
        with tempfile.TemporaryDirectory(prefix='anclicker-workspace-') as temp:
            with zipfile.ZipFile(output, 'w', zipfile.ZIP_DEFLATED, allowZip64=True) as package:
                package.writestr(MANIFEST, json.dumps(manifest, ensure_ascii=False))
                package.writestr(SETTINGS, json.dumps(settings, ensure_ascii=False))
                for root, project in zip(roots, projects):
                    part = Path(temp) / (project['id'] + '.zip')
                    export_project(db, root, part)
                    with zipfile.ZipFile(part) as incoming:
                        for item in incoming.infolist():
                            name = f"projects/{project['id']}/{item.filename}"
                            if item.is_dir():
                                package.writestr(name, b'')
                            else:
                                with incoming.open(item) as source, package.open(name, 'w', force_zip64=True) as target:
                                    shutil.copyfileobj(source, target)
                    part.unlink()
        with zipfile.ZipFile(output) as check:
            if check.testzip():
                raise ValueError('整体数据包校验失败')
        os.replace(output, archive)
    finally:
        output.unlink(missing_ok=True)
    return archive


def _read_manifest(stage):
    if not (stage / MANIFEST).is_file():
        raise ValueError('这不是整体数据包。单项目包或旧版数据包请使用“导入项目”。')
    manifest = json.loads((stage / MANIFEST).read_text(encoding='utf-8'))
    if not isinstance(manifest, dict) or manifest.get('format') != 1 or manifest.get('kind') != 'workspace':
        raise ValueError('请选择“导出整体数据”生成的数据包')
    projects = manifest.get('projects')
    if not isinstance(projects, list) or not projects:
        raise ValueError('整体数据包没有项目')
    ids = set()
    for project in projects:
        if (not isinstance(project, dict) or set(project) != {'id', 'name', 'source'}
                or not all(isinstance(value, str) for value in project.values())
                or not re.fullmatch(r'p[0-9]+', project['id']) or project['id'] in ids):
            raise ValueError('整体数据包的项目清单无效')
        ids.add(project['id'])
    if manifest.get('active') not in ids:
        raise ValueError('整体数据包的当前项目无效')
    relative = manifest.get('active_directory', '.')
    if not isinstance(relative, str) or ntpath.isabs(relative) or '..' in relative.replace('\\', '/').split('/') or ':' in relative:
        raise ValueError('整体数据包的当前项目目录无效')
    if {p.name for p in stage.iterdir()} != {MANIFEST, SETTINGS, 'projects'}:
        raise ValueError('整体数据包包含清单之外的文件')
    if {p.name for p in (stage / 'projects').iterdir()} != ids:
        raise ValueError('整体数据包项目目录与清单不一致')
    return manifest


def prepare_workspace_import(archive, parent):
    parent = Path(parent).resolve()
    stage = prepare_import(archive, parent, prefix=None)
    try:
        manifest = _read_manifest(stage)
        settings = json.loads((stage / SETTINGS).read_text(encoding='utf-8'))
        validate_global_settings(settings)
        occupied = {p.name.casefold() for p in parent.iterdir()}
        assigned = set()
        # Reserve named partitions before assigning numbers to custom folders.
        reserved = {p['name'].casefold() for p in manifest['projects'] if PARTITION.fullmatch(p['name'])}
        entries = []
        for project in manifest['projects']:
            substage = stage / 'projects' / project['id']
            if {p.name for p in substage.iterdir()} != {'Data'}:
                raise ValueError('项目包目录结构无效')
            validate_import_data(substage / 'Data')
            name = project['name']
            if not PARTITION.fullmatch(name) or name.casefold() in assigned:
                number = 1
                while f'data{number}' in occupied | assigned | reserved:
                    number += 1
                name = f'Data{number}'
            assigned.add(name.casefold())
            destination = parent / name
            if destination.is_symlink() or destination.resolve().parent != parent:
                raise ValueError(f'项目目标目录不可用：{destination}')
            entries.append(dict(project, destination=name))
        plan = dict(manifest, projects=entries)
        (stage / PLAN).write_text(json.dumps(plan, ensure_ascii=False), encoding='utf-8')
        return stage, plan
    except Exception:
        shutil.rmtree(stage)
        raise


def _relocate_global_settings(settings, projects, parent):
    """Scheduled project paths are global; map each through its own destination."""
    result = json.loads(json.dumps(settings))
    roots = sorted(projects, key=lambda item: len(item['source']), reverse=True)
    def relocate(value):
        for project in roots:
            source = ntpath.normcase(ntpath.normpath(project['source']))
            candidate = ntpath.normcase(ntpath.normpath(value))
            if candidate == source or candidate.startswith(source + '\\'):
                return str(parent / project['destination'] / ntpath.relpath(value, project['source']))
        return value
    for row in result['settings']:
        if row[1] == '定时运行任务':
            tasks = json.loads(row[2] or '[]')
            for task in tasks:
                for key in ('path', 'file_path', 'project_path'):
                    if isinstance(task.get(key), str):
                        task[key] = relocate(task[key])
            row[2] = json.dumps(tasks, ensure_ascii=False)
    return result


def apply_workspace_import(stage, parent):
    """Commit after the GUI closes; reverse all completed swaps if one fails."""
    stage, parent = Path(stage).resolve(), Path(parent).resolve()
    if stage.parent != parent or not stage.name.startswith('.anclicker-import-'):
        raise ValueError('整体导入暂存目录无效')
    plan = json.loads((stage / PLAN).read_text(encoding='utf-8'))
    entries = plan['projects']
    destinations = [parent / item['destination'] for item in entries]
    for target in destinations:
        if not PARTITION.fullmatch(target.name) or target.is_symlink() or target.resolve().parent != parent:
            raise ValueError('整体导入目标目录无效')
    settings = _relocate_global_settings(json.loads((stage / SETTINGS).read_text(encoding='utf-8')), entries, parent)
    completed = []
    try:
        for entry, destination in zip(entries, destinations):
            substage = stage / 'projects' / entry['id']
            configure_project(substage / 'Data' / '命令集.db', destination, destinations)
            backup = apply_import(substage, destination)
            completed.append((substage, destination, backup))
            write_global_settings(destination / '命令集.db', settings)
        active_entry = next(item for item in entries if item['id'] == plan['active'])
        active = parent / active_entry['destination']
        selected = active / plan.get('active_directory', '.')
        configure_project(active / '命令集.db', selected, destinations)
        select_partition(active)
    except Exception:
        for substage, destination, backup in reversed(completed):
            substage.mkdir(parents=True, exist_ok=True)
            destination.rename(substage / 'Data')
            if backup:
                backup.rename(destination)
        raise
    shutil.rmtree(stage, ignore_errors=True)
    return active
