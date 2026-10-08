"""Opt-in packaged upgrade probe; only accepts a local feed and isolated data."""
import json
import os
from pathlib import Path
import sqlite3
import velopack


def run(app, window):
    feed = Path(os.environ['ANCLICKER_SMOKE_FEED'])
    if not feed.is_absolute() or not feed.is_dir():
        raise ValueError('Smoke feed must be an existing absolute local directory')
    data = Path(os.environ['ANCLICKER_DATA_DIR'])
    marker = data / 'velopack-smoke-state.json'
    manager = velopack.UpdateManager(str(feed))
    version = str(manager.get_current_version())
    if not marker.exists():
        with sqlite3.connect(data / '命令集.db') as db:
            db.execute('CREATE TABLE velopack_retention(value TEXT)')
            db.execute("INSERT INTO velopack_retention VALUES ('preserved')")
        sentinel = data / 'images' / 'retention.txt'
        sentinel.write_text('preserved', encoding='utf-8')
        update = manager.check_for_updates()
        if update is None:
            raise RuntimeError('Local feed has no newer release')
        manager.download_updates(update)
        marker.write_text(json.dumps({'from': version, 'downloaded': True}), encoding='utf-8')
        # Exercise the actual title-button preparation path, including silent
        # editor persistence and the production updater exit logic.
        from functools import partial
        from update.自动更新 import apply_update_and_restart
        window.auto_update.apply_update = partial(apply_update_and_restart,
            source_url=str(feed), restart_args=['--velopack-local-smoke'])
        window.auto_update.mark_update_ready(update)
        window.view_workspace.title_bar.updateButton.click()
        if not getattr(window, '_update_exit_requested', False):
            raise RuntimeError('Title-bar update did not schedule a restart')
    else:
        state = json.loads(marker.read_text(encoding='utf-8'))
        if version == state['from']:
            raise RuntimeError('Updater did not switch versions')
        with sqlite3.connect(data / '命令集.db') as db:
            assert db.execute('SELECT value FROM velopack_retention').fetchone() == ('preserved',)
        assert (data / 'images' / 'retention.txt').read_text(encoding='utf-8') == 'preserved'
        state.update(to=version, restarted=True, data_preserved=True)
        (data / 'velopack-smoke-result.json').write_text(json.dumps(state), encoding='utf-8')
        app.exit(0)
