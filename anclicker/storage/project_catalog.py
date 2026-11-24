"""Known project directories for project-scoped transfer and whole-workspace backup."""
import json
from pathlib import Path
from anclicker.storage.data_partitions import partitions

CURRENT_DIRECTORY = '本机项目默认保存目录'
PROJECT_DIRECTORIES = '本机项目目录列表'


def project_root(db, folder):
    folder = Path(folder).resolve()
    data = Path(db.db_path).resolve().parent
    for partition in partitions(data.parent):
        if folder.is_relative_to(partition.resolve()):
            return partition.resolve()
    return folder


def remembered_projects(db):
    try:
        value = json.loads(db.get_setting_value(PROJECT_DIRECTORIES) or '[]')
        return [Path(item).resolve() for item in value if isinstance(item, str)] if isinstance(value, list) else []
    except (ValueError, TypeError):
        return []


def remember_project(db, folder):
    root = project_root(db, folder)
    paths = list(dict.fromkeys([*remembered_projects(db), root]))
    db.set_setting_value(PROJECT_DIRECTORIES, json.dumps([str(path) for path in paths], ensure_ascii=False))


def available_projects(db):
    data = Path(db.db_path).resolve().parent
    selected = db.get_setting_value(CURRENT_DIRECTORY)
    roots = [data, *partitions(data.parent), *remembered_projects(db)]
    if selected:
        roots.append(project_root(db, selected))
    if not roots:
        roots.append(data)
    return list(dict.fromkeys(path.resolve() for path in roots if path.is_dir() and not path.is_symlink()))
