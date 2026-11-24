"""Partition selection and consent-based project resource resolution."""
import json
import ntpath
import os
import re
from pathlib import Path

PARTITION = re.compile(r'Data(?:[1-9][0-9]*)?', re.I)
SELECTION = '.active-data.json'

def next_partition(root):
    root = Path(root).resolve()
    number = 1
    occupied = {p.name.casefold() for p in root.iterdir()}
    while f'data{number}' in occupied:
        number += 1
    return root / f'Data{number}'

def selected_partition(root):
    root = Path(root).resolve()
    try:
        name = json.loads((root / SELECTION).read_text(encoding='utf-8'))['directory']
        target = root / name
        if PARTITION.fullmatch(name) and not target.is_symlink() and target.resolve().is_relative_to(root) and (target / '命令集.db').is_file():
            return target
    except (OSError, ValueError, TypeError, KeyError):
        pass
    return root / 'Data'

def select_partition(folder):
    folder = Path(folder).resolve()
    if not PARTITION.fullmatch(folder.name):
        raise ValueError('分区目录必须使用 Data、Data1、Data2…')
    target = folder.parent / SELECTION
    temporary = target.with_suffix('.tmp')
    temporary.write_text(json.dumps({'directory': folder.name}), encoding='utf-8')
    temporary.replace(target)

def partitions(root):
    root = Path(root).resolve()
    return sorted((p for p in root.iterdir() if PARTITION.fullmatch(p.name) and p.is_dir()
                   and not p.is_symlink() and p.resolve().is_relative_to(root)), key=lambda p:p.name)

def project_partition(project, root):
    project = Path(project).resolve()
    return next((p for p in partitions(root) if project.is_relative_to(p.resolve())), None)

def original_reference(value, project, data):
    """Resolve relative spelling without rewriting it or doing a filename search."""
    path = Path(value.replace('\\', '/'))
    if ntpath.isabs(value):
        return path if path.exists() else None
    for base in (Path(project).parent, Path(data)):
        candidate = base / path
        if candidate.exists():
            return candidate.resolve()
    return None


def bounded_entries(base):
    base = Path(base).resolve()
    for directory, dirs, files in os.walk(base, followlinks=False):
        dirs[:] = [name for name in dirs if name != 'migration_backups'
                   and not (Path(directory)/name).is_symlink()
                   and not getattr(Path(directory)/name, 'is_junction', lambda:False)()
                   and (Path(directory)/name).resolve().is_relative_to(base)]
        for name in dirs + files:
            path = Path(directory) / name
            if not path.is_symlink() and path.resolve().is_relative_to(base):
                yield path

def find_adaptation(value, root, preferred=None):
    """Search only Data partitions inside this application; never follow links out."""
    root = Path(root).resolve()
    roots = partitions(root)
    preferred = Path(preferred).resolve() if preferred else None
    if preferred and preferred.is_dir() and preferred not in roots:
        roots.insert(0, preferred)
    tiers = [[p for p in roots if p.resolve() == preferred], [p for p in roots if p.resolve() != preferred]]
    parts = value.replace('\\', '/').split('/')
    tail = next((parts[i+1:] for i in range(len(parts)-1, -1, -1) if PARTITION.fullmatch(parts[i])), None)
    name = ntpath.basename(value)
    for group in tiers:
        matches = set()
        for base in group:
            from anclicker.storage.data_bundle import directory_path, load_mappings
            mapped = directory_path(value, base, load_mappings(base))
            if mapped != value and Path(mapped).resolve().is_relative_to(base):
                matches.add(Path(mapped).resolve())
            if tail and not any(p in ('.','..') for p in tail):
                candidate = base.joinpath(*tail).resolve()
                if candidate.is_relative_to(base.resolve()) and candidate.exists():
                    matches.add(candidate)
        if not matches:
            for base in group:
                matches.update(p.resolve() for p in bounded_entries(base)
                               if p.name.casefold() == name.casefold() and p.resolve().is_relative_to(base.resolve())
                               and 'migration_backups' not in p.parts)
        if len(matches) > 1:
            raise ValueError(f'存在多个同名候选，未自动适配：{value}\n' + '\n'.join(map(str, sorted(matches))))
        if matches:
            return str(matches.pop())
    raise ValueError(f'当前 AnClicker 的 Data 分区内未找到：{value}')

def workbook_references(book):
    from anclicker.storage.data_bundle import input_keys
    generated = set()
    for row in book['命令'].iter_rows(min_row=2):
        if row[0].value is None:
            continue
        parameters = json.loads(row[2].value)
        for key in input_keys(row[1].value):
            value = parameters.get(key)
            if isinstance(value, str) and '{{' not in value and '☾' not in value:
                for line in value.splitlines():
                    if line.strip() and line.replace(chr(92),'/').casefold() not in generated:
                        yield row[2], key, line
        output_keys = {'保存路径', 'toPath', '目标路径', 'dst'}
        if row[1].value in ('新建Excel','保存Excel','网页截图','抓取导出Excel'):
            output_keys.add('path')
        for key in output_keys:
            value = parameters.get(key)
            if isinstance(value,str) and value:
                generated.add(value.replace(chr(92),'/').casefold())

def prepare_project_paths(book, project, data, root, confirm):
    """Rebase exact project references automatically; ambiguous legacy paths need selection."""
    from anclicker.storage.project_paths import project_root, resolve_parameters, resolve_path, input_keys, path_lines, map_workbook_resources, map_background_paths
    from anclicker.storage.data_bundle import _inputs
    preferred = project_root(project, data)
    planned, missing, generated = [], set(), set()
    for row in book['命令'].iter_rows(min_row=2):
        if row[0].value is None:
            continue
        original = json.loads(row[2].value)
        values = resolve_parameters(original, row[1].value, preferred, base=Path(project).parent)
        missing.update(value for value in _inputs(values, row[1].value, generated) if not Path(value).exists())
        planned.append((row[2], row[1].value, original, values))
    changes = {}
    if missing:
        if not confirm(sorted(missing)):
            return False
        changes = {value:find_adaptation(value, root, preferred) for value in missing}
    for cell, kind, original, values in planned:
        for key in input_keys(kind):
            if isinstance(values.get(key), str):
                values[key] = '\n'.join(changes.get(line, line) for line in path_lines(values[key], kind))
        values = map_background_paths(values, kind, lambda value, output: value if output else changes.get(value, value))
        if values != original:
            cell.value = json.dumps(values, ensure_ascii=False)
    map_workbook_resources(book, lambda value: resolve_path(value, preferred, base=Path(project).parent))
    return True


def bundle_needs_adaptation(data):
    from anclicker.storage.data_bundle import _database_inputs, _workbook_inputs
    data = Path(data)
    values = [(value, data) for value in _database_inputs(data / '命令集.db')]
    for project in data.rglob('*'):
        if project.suffix.lower() in ('.xlsx','.xlsm') and 'migration_backups' not in project.parts and not project.name.startswith('~$'):
            values.extend((value, project.parent) for value in _workbook_inputs(project))
    return any(original_reference(value, base / '_project.xlsx', data) is None for value,base in values)


def adapt_bundle(data, destination, root):
    """Repair missing input paths in staging only; commit/restart is separate."""
    import contextlib
    import sqlite3
    import openpyxl
    from anclicker.storage.data_bundle import input_keys
    from anclicker.storage.portable_migration import relocated_path
    data, destination = Path(data).resolve(), Path(destination).resolve()
    def adapt(value, project):
        if not isinstance(value,str) or not value or '{{' in value or '☾' in value:
            return value
        if original_reference(value, project, data) is not None:
            return value
        candidate = Path(relocated_path(value, data))
        if candidate.exists() and candidate.resolve().is_relative_to(data):
            return str(destination / candidate.resolve().relative_to(data))
        matches = {p.resolve() for p in bounded_entries(data) if p.name.casefold() == ntpath.basename(value).casefold()
                   and p.resolve().is_relative_to(data) and 'migration_backups' not in p.parts}
        if len(matches) > 1:
            raise ValueError(f'导入数据中存在多个同名资源，未适配：{value}')
        if matches:
            return str(destination / matches.pop().relative_to(data))
        return find_adaptation(value, root, destination)
    def parameters(value, kind, project):
        result = json.loads(value)
        for key in input_keys(kind):
            if isinstance(result.get(key), str):
                result[key] = '\n'.join(adapt(line,project) for line in result[key].splitlines())
        return json.dumps(result, ensure_ascii=False)
    with contextlib.closing(sqlite3.connect(str(data / '命令集.db'))) as conn:
        with conn:
            for command_id,kind,value in list(conn.execute('SELECT ID,类型标识,参数JSON FROM 命令')):
                conn.execute('UPDATE 命令 SET 参数JSON=? WHERE ID=?',(parameters(value,kind,data/'_project.xlsx'),command_id))
            for name,value in list(conn.execute('SELECT 变量名称,值 FROM 变量池')):
                if isinstance(value,str) and ntpath.isabs(value):
                    # Only known mapped resources; arbitrary text variables stay untouched.
                    mapped = relocated_path(value,data)
                    if mapped != value:
                        conn.execute('UPDATE 变量池 SET 值=? WHERE 变量名称=?',(adapt(value,data/'_project.xlsx'),name))
    for project in list(data.rglob('*')):
        if project.suffix.lower() not in ('.xlsx','.xlsm') or 'migration_backups' in project.parts or project.name.startswith('~$'):
            continue
        book = openpyxl.load_workbook(project, keep_vba=project.suffix.lower()=='.xlsm')
        try:
            if {'命令','节点','连线','设置'} <= set(book.sheetnames):
                for row in book['命令'].iter_rows(min_row=2):
                    if row[0].value is not None:
                        row[2].value = parameters(row[2].value,row[1].value,project)
                book.save(project)
        finally:
            book.close()


def ensure_runtime_paths(window):
    """Give copied/restored projects the same consent gate before execution."""
    import contextlib
    import sqlite3
    from openpyxl import Workbook
    from anclicker.platform.qt_compat.QtWidgets import QMessageBox
    if getattr(window, '_adapting_paths', False):
        return False
    db = getattr(window, 'db', None)
    if db is None or not getattr(db,'db_path',None):
        return True
    data = Path(db.db_path).resolve().parent
    project = db.get_setting_value('当前文件路径')
    if not project or project == 'None':
        project = str(data / '_project.xlsx')
    book = Workbook()
    sheet = book.active
    sheet.title = '命令'
    sheet.append(['ID','类型标识','参数JSON'])
    try:
        with contextlib.closing(sqlite3.connect(db.db_path)) as conn:
            original = list(conn.execute('SELECT ID,类型标识,参数JSON FROM 命令'))
        for row in original:
            sheet.append(row)
        window._adapting_paths = True
        if not prepare_project_paths(book,project,data,data.parent,
                lambda missing: QMessageBox.question(window,'是否适配资源路径',
                    f'有 {len(missing)} 个资源路径不可用。是否在当前 AnClicker 的 Data 分区内查找并适配？',
                    QMessageBox.Yes | QMessageBox.No,QMessageBox.No)==QMessageBox.Yes):
            return False
        changes = [(sheet.cell(i+2,3).value,row[0]) for i,row in enumerate(original) if sheet.cell(i+2,3).value != row[2]]
        if changes:
            with contextlib.closing(sqlite3.connect(db.db_path)) as conn:
                with conn:
                    conn.executemany('UPDATE 命令 SET 参数JSON=? WHERE ID=?',changes)
            window.workspace.reload_graph(reset_view=False)
            window.view_workspace.refresh_all()
        return True
    except (ValueError,OSError,sqlite3.Error) as error:
        QMessageBox.warning(window,'资源路径未适配',str(error))
        return False
    finally:
        window._adapting_paths = False
        book.close()
