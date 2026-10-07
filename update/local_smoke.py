"""Explicit, isolated local-source update acceptance hook. No automation commands run."""
import json
import os
import sqlite3
import sys
from pathlib import Path

def run_update_smoke():
    import velopack
    source = Path(os.environ['ANCLICKER_LOCAL_UPDATE_SOURCE']).resolve()
    if not source.is_dir():
        raise ValueError('本地升级验收需要已有本地目录')
    data = Path(os.environ['ANCLICKER_DATA_DIR'])
    root = Path(sys.executable).parent.parent
    if data.resolve() != (root / 'data').resolve():
        raise ValueError('本地升级验收必须使用 Portable 外侧 data')
    from 数据库操作 import DatabaseOperation
    db = DatabaseOperation(str(data / '命令集.db'))
    manager = velopack.UpdateManager(str(source))
    version = str(manager.get_current_version())
    with sqlite3.connect(db.db_path) as con:
        if not (data / 'update-before.json').exists():
            con.execute('CREATE TABLE upgrade_sentinel (value TEXT)')
            con.execute("INSERT INTO upgrade_sentinel VALUES ('preserved')")
        if con.execute('SELECT value FROM upgrade_sentinel').fetchone() != ('preserved',):
            raise RuntimeError('升级丢失数据库')
    marker = data / 'user-sentinel.txt'
    if not marker.exists():
        marker.write_text('preserved', encoding='utf-8')
    if marker.read_text(encoding='utf-8') != 'preserved':
        raise RuntimeError('升级丢失用户文件')
    update = manager.check_for_updates()
    if update is not None:
        (data / 'update-before.json').write_text(json.dumps({'version': version}), encoding='utf-8')
        manager.download_updates(update)
        manager.apply_updates_and_restart_with_args(update, ['--release-update-smoke'])
    else:
        (data / 'update-after.json').write_text(json.dumps({'version': version, 'database_preserved': True,
            'file_preserved': True, 'data_root': str(data)}), encoding='utf-8')
    return 0
