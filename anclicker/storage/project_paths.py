"""Path fields have a project/page base, independent of the process working directory."""
import ntpath
import os
from pathlib import Path
import re
import json

INPUT_KEYS = {'图像路径', '图像', '图片', '工作簿', '文件路径', '项目路径',
              '是项目路径', '否项目路径', 'fromPath', '题库路径', '源路径', 'folder'}
OUTPUT_KEYS = {'保存路径', '输出路径', 'toPath', '目标路径', 'dst'}
PARTITION = re.compile(r'(?:Data(?:[1-9][0-9]*)?|Date)', re.I)


def input_keys(command_type=''):
    keys = set(INPUT_KEYS)
    if command_type == '打开Excel':
        keys.add('path')
    if command_type == '运行外部文件':
        keys.add('路径')
    if command_type == '字库点击':
        keys.add('字库目录')
    if command_type == 'A星寻路':
        keys.add('地图路径')
    return keys


def output_keys(command_type=''):
    keys = set(OUTPUT_KEYS)
    if command_type in {'新建Excel', '保存Excel', '网页截图', '抓取导出Excel'}:
        keys.add('path')
    if command_type == '屏幕截图':
        keys.add('路径')
    return keys


def literal_path(value):
    return (isinstance(value, str) and bool(value.strip()) and '{{' not in value and '☾' not in value
            and not re.match(r'^[a-zA-Z][a-zA-Z0-9+.-]*://', value))


def path_lines(value, command_type=''):
    if command_type == '多图点击':
        value = value.replace(';', '\n').replace('、', '\n')
    return value.splitlines()


def background_paths(parameters, command_type):
    """Only declared file arguments inside background-method JSON are paths."""
    if not command_type.startswith('后台') or not isinstance(parameters.get('参数'), str):
        return {}, {}
    try:
        values = json.loads(parameters['参数'])
    except ValueError:
        return {}, {}
    if not isinstance(values, dict):
        return {}, {}
    method = str(parameters.get('接口', '')).strip().rsplit(' · ', 1)[-1].casefold()
    fields = {}
    if method.startswith('findpic') or method in {'ocrinfile', 'loadpic', 'freepic', 'getpicsize',
                                               'imagetobmp', 'createfoobarcustom', 'foobardrawpic'}:
        fields.update(pic_name=False, pic=False)
    if method == 'setpath':
        fields['path'] = False
    elif method == 'setdict':
        fields['dict_name'] = False
    elif method in {'savedict', 'capture', 'capturepng', 'capturejpg', 'capturegif'}:
        fields['file'] = True
    elif method == 'imagetobmp':
        fields['bmp_name'] = True
    elif method in {'encodefile', 'decodefile'}:
        fields['file'] = False
    return values, {key: output for key, output in fields.items() if isinstance(values.get(key), str)}


def map_background_paths(parameters, command_type, transform):
    values, fields = background_paths(parameters, command_type)
    if not fields:
        return parameters
    changed = False
    for key, output in fields.items():
        delimiter = '|' if key in ('pic_name', 'pic') else '\n'
        new = delimiter.join(transform(value, output) for value in values[key].split(delimiter))
        changed |= new != values[key]
        values[key] = new
    return dict(parameters, 参数=json.dumps(values, ensure_ascii=False)) if changed else parameters


def declared_outputs(parameters, command_type):
    yield from (parameters[key] for key in output_keys(command_type) if literal_path(parameters.get(key)))
    values, fields = background_paths(parameters, command_type)
    yield from (values[key] for key, output in fields.items() if output and literal_path(values[key]))


def project_root(project=None, data=None, selected=None):
    data = Path(data).resolve() if data else None
    page = Path(project).resolve() if project and project != 'None' else None
    if page:
        for parent in page.parents:
            if (parent / 'portable-directories.json').is_file() or PARTITION.fullmatch(parent.name):
                return parent
        if selected and page.is_relative_to(Path(selected).resolve()):
            return Path(selected).resolve()
        return page.parent
    return Path(selected).resolve() if selected else data


def mapped_path(value, root, *, output=False, mappings=None):
    """Exact manifest mapping first, even if the author's original path still exists."""
    if not literal_path(value) or root is None:
        return value
    from anclicker.storage.data_bundle import load_mappings
    mappings = load_mappings(root) if mappings is None else mappings
    root = Path(root).resolve()
    normalized = value.replace('\\', '/').rstrip('/')
    for old, relative in sorted(mappings.items(), key=lambda item: -len(item[0])):
        old = old.replace('\\', '/').rstrip('/')
        if normalized.casefold() == old.casefold() or normalized.casefold().startswith(old.casefold() + '/'):
            target = (root / relative / normalized[len(old):].lstrip('/')).resolve()
            if target.is_relative_to(root) and (output or target.exists()):
                return str(target)
    return value


def resolve_path(value, root, *, base=None, output=False, fallback=None, mappings=None):
    if not literal_path(value) or root is None:
        return value
    root = Path(root).resolve()
    base = Path(base).resolve() if base else root
    mapped = mapped_path(value, root, output=output, mappings=mappings)
    if mapped != value:
        return mapped
    path = Path(value.replace('\\', '/'))
    if not ntpath.isabs(value):
        target = (base / path).resolve()
        if not output and not target.exists():
            for alternative in (root, fallback):
                if alternative is not None and (Path(alternative) / path).exists():
                    return str((Path(alternative) / path).resolve())
        return str(target)
    if path.exists() or path.resolve().is_relative_to(root):
        return str(path.resolve())
    # Legacy packages may have no manifest. Preserve the tail of Data/DataN.
    parts = value.replace('\\', '/').split('/')
    candidates = set()
    for index, part in enumerate(parts):
        if PARTITION.fullmatch(part) or part.casefold() == root.name.casefold():
            tail = parts[index + 1:]
            if not tail or any(p in ('.', '..') for p in tail):
                continue
            target = root.joinpath(*tail).resolve()
            if target.is_relative_to(root) and (output or target.exists()):
                candidates.add(target)
    return str(candidates.pop()) if len(candidates) == 1 else value


def resolve_parameters(parameters, command_type, root, *, base=None, fallback=None, substitute=None):
    result = dict(parameters)
    outputs = output_keys(command_type)
    for key in input_keys(command_type) | outputs:
        value = result.get(key)
        if not isinstance(value, str):
            continue
        if substitute:
            value = substitute(value)
        result[key] = '\n'.join(resolve_path(line, root, base=base, fallback=fallback, output=key in outputs)
                                for line in path_lines(value, command_type))
    return map_background_paths(result, command_type, lambda value, output: resolve_path(
        substitute(value) if substitute else value, root, base=base, fallback=fallback, output=output))


def relative_parameters(parameters, command_type, root, base, *, mappings=None, external_outputs=False):
    """Encode package paths relative to each workbook (or the active database page)."""
    import hashlib
    result = dict(parameters)
    root, base = Path(root).resolve(), Path(base).resolve()
    outputs = output_keys(command_type)
    for key in input_keys(command_type) | outputs:
        value = result.get(key)
        if not isinstance(value, str):
            continue
        lines = []
        for line in path_lines(value, command_type):
            # Generated output files need not exist yet, including subsequent reads.
            mapped = mapped_path(line, root, output=True, mappings=mappings)
            if literal_path(mapped) and ntpath.isabs(mapped):
                path = Path(mapped).resolve()
                if key in outputs and external_outputs and not path.is_relative_to(root):
                    name = ntpath.basename(line)
                    parent = ntpath.dirname(line)
                    path = root / 'outputs' / hashlib.sha256(parent.encode('utf-8')).hexdigest()[:12] / name
                    # A following read of the generated file must use this same mapping.
                    if mappings is not None:
                        mappings[line] = path.relative_to(root).as_posix()
                if path.is_relative_to(root):
                    mapped = Path(os.path.relpath(path, base)).as_posix()
            lines.append(mapped)
        result[key] = '\n'.join(lines)
    return map_background_paths(result, command_type, lambda value, output: relative_parameters(
        {'保存路径' if output else '文件路径': value}, '', root, base, mappings=mappings,
        external_outputs=external_outputs)['保存路径' if output else '文件路径'])


def runtime_parameters(context, command):
    if not ((input_keys(command.type_id) | output_keys(command.type_id)).intersection(command.parameters)
            or background_paths(command.parameters, command.type_id)[1]):
        return command.parameters
    database = getattr(getattr(context, 'runtime', None), 'database', None) or context.metadata.get('database')
    getter = getattr(database, 'get_setting_value', lambda key: None)
    project = context.metadata.get('project_path') or getter('当前文件路径')
    data = Path(database.db_path).parent if getattr(database, 'db_path', None) else None
    root = project_root(project, data, getter('本机项目默认保存目录'))
    if root is None:
        return command.parameters
    from anclicker.execution.actions import substitute_variables
    base = Path(project).resolve().parent if project and project != 'None' else root
    values = resolve_parameters(command.parameters, command.type_id, root, base=base,
                                substitute=lambda value: substitute_variables(context, value))
    for value in declared_outputs(values, command.type_id):
        if literal_path(value) and '\n' not in value:
            Path(value).parent.mkdir(parents=True, exist_ok=True)
    return values


def save_workbook_paths(book, source, destination, root, *, fallback=None):
    """Save As rebases relative paths without changing the live command records."""
    source_base = Path(source).parent if source and source != 'None' else Path(root)
    target_base = Path(destination).resolve().parent
    for row in book['命令'].iter_rows(min_row=2):
        if row[0].value is None:
            continue
        values = resolve_parameters(json.loads(row[2].value), row[1].value, root, base=source_base, fallback=fallback)
        row[2].value = json.dumps(relative_parameters(values, row[1].value, root, target_base), ensure_ascii=False)
    map_workbook_resources(book, lambda value: relative_parameters(
        {'folder': resolve_path(value, root, base=source_base, fallback=fallback)}, '', root, target_base)['folder'])


def map_workbook_resources(book, transform):
    """Two old resource spellings may collapse to the same local directory."""
    if '设置' not in book:
        return False
    sheet, seen, duplicates, changed = book['设置'], set(), [], False
    for row in sheet.iter_rows(min_row=2):
        if row[0].value != '资源文件夹':
            continue
        value = transform(row[1].value)
        key = ntpath.normcase(ntpath.normpath(value))
        if key in seen:
            duplicates.append(row[0].row)
        else:
            seen.add(key)
            changed |= value != row[1].value
            row[1].value = value
    for index in reversed(duplicates):
        sheet.delete_rows(index)
    return changed or bool(duplicates)


def rebase_saved_commands(db, source, destination, root):
    """Keep the live database referring to the same files after Save As changes its page base."""
    if source and source != 'None' and Path(source).resolve().parent == Path(destination).resolve().parent:
        return
    import contextlib
    import json
    import sqlite3
    base = Path(source).parent if source and source != 'None' else Path(root)
    with contextlib.closing(sqlite3.connect(db.db_path)) as conn, conn:
        for command_id, kind, raw in list(conn.execute('SELECT ID, 类型标识, 参数JSON FROM 命令')):
            values = resolve_parameters(json.loads(raw), kind, root, base=base, fallback=Path(db.db_path).parent)
            if values != json.loads(raw):
                conn.execute('UPDATE 命令 SET 参数JSON=? WHERE ID=?', (json.dumps(values, ensure_ascii=False), command_id))
