"""Isolated portable migration regression; never touches personal Data."""
import contextlib
import json
import os
from pathlib import Path
import sqlite3
import sys
import tempfile
sys.path.insert(0, str(Path(__file__).resolve().parents[1]))
from anclicker.storage.portable_migration import copied_data_folder, relocated_path, relocate_database

with tempfile.TemporaryDirectory() as temporary:
    root = Path(temporary)
    data = root / '新版' / 'Data'
    project = data / 'exports' / '指令数据4.xlsx'
    project.parent.mkdir(parents=True)
    project.write_bytes(b'project sentinel')
    old = str(root / '旧版' / 'Data' / 'exports' / project.name)
    Path(old).parent.mkdir(parents=True)
    Path(old).write_bytes(b'old sentinel')
    assert relocated_path(old, data) == str(project)  # do not keep opening old project
    assert relocated_path('Z:/old/Data/exports/指令数据4.xlsx', data) == str(project)
    assert relocated_path('Z:/old/date/exports/指令数据4.xlsx', data) == str(project)
    assert relocated_path('Z:/old/Data/../secret', data) == 'Z:/old/Data/../secret'
    assert relocated_path('Z:/external/指令数据4.xlsx', data) == 'Z:/external/指令数据4.xlsx'
    missing = 'Z:/old/Data/exports/missing.xlsx'
    assert relocated_path(missing, data) == missing
    db = data / '命令集.db'
    with contextlib.closing(sqlite3.connect(db)) as conn:
        conn.executescript('CREATE TABLE 最近打开(文件路径 TEXT, 打开时间 INTEGER); CREATE TABLE 资源文件夹(路径 TEXT PRIMARY KEY, 排序 INTEGER); CREATE TABLE 设置(设置项 TEXT PRIMARY KEY, 值 TEXT); CREATE TABLE 指令(内容 TEXT);')
        conn.execute('INSERT INTO 最近打开 VALUES (?, 123)', (old,))
        conn.execute('INSERT INTO 资源文件夹 VALUES (?, 1)', (str(Path(old).parent),))
        settings = {'当前文件路径': old, '本机新建默认保存路径': old,
                    '本机项目控制设置': json.dumps({os.path.normcase(old): {'运行重复次数': '7'}}),
                    '本机项目已保存内容': json.dumps({'path': os.path.normcase(old), 'digest': 'saved'}),
                    '定时运行任务': json.dumps([{'path': old, 'repeat': '每天', 'next_run': '2026-11-02T12:00:00'}]),
                    '界面主题': 'dark'}
        conn.executemany('INSERT INTO 设置 VALUES (?, ?)', settings.items())
        conn.execute('INSERT INTO 指令 VALUES (?)', (old,))
        conn.commit()
    assert relocate_database(db, data) == 7
    assert relocate_database(db, data) == 0
    with contextlib.closing(sqlite3.connect(db)) as conn:
        values = dict(conn.execute('SELECT * FROM 设置'))
        assert values['当前文件路径'] == str(project)
        assert json.loads(values['本机项目控制设置'])[os.path.normcase(str(project))]['运行重复次数'] == '7'
        assert json.loads(values['本机项目已保存内容']) == {'path': os.path.normcase(str(project)), 'digest': 'saved'}
        assert json.loads(values['定时运行任务'])[0]['path'] == str(project)
        assert values['界面主题'] == 'dark'
        assert conn.execute('SELECT * FROM 最近打开').fetchone() == (str(project), 123)
        assert conn.execute('SELECT * FROM 指令').fetchone()[0] == old
    backups = list((data / 'migration_backups').glob('*.db'))
    assert len(backups) == 1
    with contextlib.closing(sqlite3.connect(backups[0])) as conn:
        assert dict(conn.execute('SELECT * FROM 设置'))['当前文件路径'] == old
    assert Path(old).read_bytes() == b'old sentinel'
    assert project.read_bytes() == b'project sentinel'
    outer = root / 'nested' / 'Data'
    inner = outer / 'Data'
    inner.mkdir(parents=True)
    (inner / '命令集.db').write_bytes(b'sentinel')
    assert copied_data_folder(outer) == str(inner)
    (outer / '命令集.db').write_bytes(b'existing')
    assert copied_data_folder(outer) == str(outer)
print('PASS copied Data migration: projects, controls, saved state, schedules, backup, idempotence, nested folder, conflict protection')

# Exercise the real startup initialization in a fresh process for both copy forms.
import subprocess
for nested in (False, True):
    with tempfile.TemporaryDirectory() as temporary:
        outer = Path(temporary) / 'Data'
        active = outer / 'Data' if nested else outer
        active.mkdir(parents=True)
        project = active / 'exports' / '迁移.xlsx'
        project.parent.mkdir()
        project.write_bytes(b'project')
        with contextlib.closing(sqlite3.connect(active / '命令集.db')) as conn:
            conn.execute('CREATE TABLE 设置(设置项 TEXT, 值 TEXT)')
            conn.execute('INSERT INTO 设置 VALUES (?, ?)', ('当前文件路径', 'Z:/old/Data/exports/迁移.xlsx'))
            conn.commit()
        env = dict(os.environ, ANCLICKER_DATA_DIR=str(outer), QT_QPA_PLATFORM='offscreen', PYTHONDONTWRITEBYTECODE='1')
        code = "from anclicker.app.startup_environment import prepare_environment; prepare_environment(); from anclicker.app.paths import ensure_data_directories, DATA_FOLDER; ensure_data_directories(); from anclicker.storage.database import DatabaseOperation; from pathlib import Path; db=DatabaseOperation(); assert Path(db.get_setting_value('当前文件路径')) == Path(DATA_FOLDER)/'exports'/'迁移.xlsx'; print('PASS actual startup')"
        for _ in range(2):
            result = subprocess.run([sys.executable, '-B', '-X', 'utf8', '-c', code], cwd=Path(__file__).resolve().parents[1], env=env, capture_output=True, text=True, encoding='utf8', timeout=60)
            assert result.returncode == 0, result.stdout + result.stderr
        assert len(list((active / 'migration_backups').glob('*.db'))) == 1
print('PASS real database startup: direct/nested Data, repeat launch')
