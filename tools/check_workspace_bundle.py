"""Multiple projects, shared settings, portable restore and rollback regression."""
import contextlib
import json
import os
from pathlib import Path
import shutil
import sqlite3
import sys
import tempfile
from unittest.mock import patch
import zipfile
from openpyxl import Workbook

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))
from anclicker.storage.database import DatabaseOperation
from anclicker.storage.graph_repository import GraphRepository
from anclicker.storage.data_bundle import prepare_import, apply_import
from anclicker.storage.data_partitions import selected_partition
from anclicker.storage.project_catalog import remember_project, CURRENT_DIRECTORY
from anclicker.storage.workspace_bundle import (export_project, export_workspace, prepare_workspace_import,
    apply_workspace_import, read_global_settings, write_global_settings, MANIFEST)
from anclicker.domain.instructions import InstructionDraft


def page(db, folder, name):
    db.set_setting_value('任务名称', name)
    file = folder / (name + '.xlsx')
    book = Workbook()
    GraphRepository(db.db_path).export_to_workbook(book, db)
    book.save(file)
    book.close()
    return file


with tempfile.TemporaryDirectory() as directory:
    root = Path(directory)
    source = root / 'source'
    data, data2, custom = source / 'Data', source / 'Data2', root / 'custom'
    for folder in (data, data2, custom):
        folder.mkdir(parents=True)
    db = DatabaseOperation(str(data / '命令集.db'))
    other = DatabaseOperation(str(data2 / '命令集.db'))
    first = page(db, data, '项目一')
    second = page(other, data2, '项目二旧页')
    page(other, custom, '外部项目')
    (custom / '说明.txt').write_text('custom', encoding='utf-8')
    db.set_setting_values({CURRENT_DIRECTORY: str(data2), '当前文件路径': str(second),
                           '任务名称': '项目二未保存', '界面主题': 'dark', '快捷键-开始运行': 'f9',
                           '定时运行任务': json.dumps([{'path': str(first), 'enabled': False}])})
    db.save_window_size(960, 720, '主界面', position=(100, 120))
    image = data2 / 'images' / '图像.png'
    image.parent.mkdir()
    image.write_bytes(b'project-2-image')
    GraphRepository(db.db_path).append_recording([InstructionDraft('图像点击', {'图像路径': str(image)})])
    shared = data / 'images' / '共享.png'
    shared.parent.mkdir()
    shared.write_bytes(b'shared-image')
    with contextlib.closing(sqlite3.connect(db.db_path)) as conn, conn:
        row = conn.execute('SELECT ID, 参数JSON FROM 命令').fetchone()
        params = json.loads(row[1])
        params['fromPath'] = 'images/共享.png'
        conn.execute('UPDATE 命令 SET 参数JSON=? WHERE ID=?', (json.dumps(params), row[0]))
    remember_project(db, custom)
    original_globals = read_global_settings(db.db_path)
    project_zip = export_project(db, data2, root / 'project.zip')
    stage = prepare_import(project_zip, root)
    with contextlib.closing(sqlite3.connect(str(stage / 'Data' / '命令集.db'))) as conn:
        values = dict(conn.execute('SELECT 设置项, 值 FROM 设置'))
        assert values['任务名称'] == '项目二未保存'
        assert '界面主题' not in values and '快捷键-开始运行' not in values
        assert conn.execute('SELECT count(*) FROM 命令').fetchone()[0] == 1
        assert conn.execute('SELECT count(*) FROM 窗口大小').fetchone()[0] == 0
    assert not (stage / 'Data' / first.name).exists()
    write_global_settings(stage / 'Data' / '命令集.db', original_globals)
    assert read_global_settings(stage / 'Data' / '命令集.db') == original_globals
    shutil.rmtree(stage)

    archive = export_workspace(db, root / 'all.zip')
    with zipfile.ZipFile(archive) as package:
        manifest = json.loads(package.read(MANIFEST))
        assert len(manifest['projects']) == 3
        assert manifest['active'] == 'p1'
        assert not any(name.endswith('.zip') for name in package.namelist())
    # Export is read-only, including global preferences and unsaved project data.
    assert read_global_settings(db.db_path) == original_globals
    assert db.get_setting_value('任务名称') == '项目二未保存'
    source.rename(root / 'offline-source')
    custom.rename(root / 'offline-custom')
    target = root / 'target'
    target.mkdir()
    for name in ('Data', 'Data2', 'Data9'):
        (target / name).mkdir()
        (target / name / 'keep.txt').write_text(name)
    stage, plan = prepare_workspace_import(archive, target)
    assert [p['destination'] for p in plan['projects']] == ['Data', 'Data2', 'Data1']
    active = apply_workspace_import(stage, target)
    assert active == target / 'Data2' and selected_partition(target) == active
    assert (target / 'Data9' / 'keep.txt').read_text() == 'Data9'
    for name in ('Data', 'Data2'):
        backups = list(target.glob(name + '-导入前备份-*'))
        assert len(backups) == 1 and (backups[0] / 'keep.txt').read_text() == name
    restored = DatabaseOperation(str(active / '命令集.db'))
    assert restored.get_setting_value('任务名称') == '项目二未保存'
    assert restored.get_setting_value('界面主题') == 'dark'
    assert restored.get_setting_value(CURRENT_DIRECTORY) == str(active)
    assert restored.get_window_state('主界面')['position'] == (100, 120)
    assert restored.get_setting_value('当前文件路径') == str(active / second.name)
    schedule = json.loads(restored.get_setting_value('定时运行任务'))
    assert schedule[0]['path'] == str(target / 'Data' / first.name)
    with contextlib.closing(sqlite3.connect(restored.db_path)) as conn:
        parameters = json.loads(conn.execute('SELECT 参数JSON FROM 命令').fetchone()[0])
        assert Path(parameters['图像路径']).read_bytes() == b'project-2-image'
        assert Path(parameters['图像路径']).is_relative_to(active)
        assert Path(parameters['fromPath']).read_bytes() == b'shared-image'
        assert Path(parameters['fromPath']).is_relative_to(active)
    inactive = DatabaseOperation(str(target / 'Data' / '命令集.db'))
    assert not GraphRepository(inactive.db_path).list_commands()  # no active Data2 graph duplicated into Data
    assert (target / 'Data1' / '说明.txt').read_text(encoding='utf-8') == 'custom'

    # A failure after the first swap restores every old project and active selection.
    before = {name: (target / name / '命令集.db').read_bytes() for name in ('Data', 'Data2')}
    selection = (target / '.active-data.json').read_bytes()
    stage, _ = prepare_workspace_import(archive, target)
    original_apply = apply_import
    calls = 0
    def failing_apply(*args, **kwargs):
        global calls
        calls += 1
        if calls == 2:
            raise OSError('injected second-project failure')
        return original_apply(*args, **kwargs)
    with patch('anclicker.storage.workspace_bundle.apply_import', side_effect=failing_apply):
        try:
            apply_workspace_import(stage, target)
        except OSError:
            pass
        else:
            raise AssertionError('expected failure')
    for name, content in before.items():
        assert (target / name / '命令集.db').read_bytes() == content
    assert (target / '.active-data.json').read_bytes() == selection
    shutil.rmtree(stage)

    for entry in ('../escape', 'projects/p0/Data/../../escape'):
        malicious = root / 'malicious.zip'
        with zipfile.ZipFile(malicious, 'w') as package:
            package.writestr(entry, b'bad')
        try:
            prepare_workspace_import(malicious, target)
        except ValueError:
            pass
        else:
            raise AssertionError('unsafe archive accepted')
    try:
        prepare_workspace_import(project_zip, target)
    except (ValueError, FileNotFoundError):
        pass
    else:
        raise AssertionError('single project accepted as whole workspace')
    assert not list(target.glob('.anclicker-import-*'))
print('PASS selected project scope, unsaved active graph, all projects/settings, flat ZIP, offline resource relocation, backup, active project, rollback and invalid archive rejection')
