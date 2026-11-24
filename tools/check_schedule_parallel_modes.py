"""Exercise real workers with synthetic instructions and isolated project files."""
import os
import sys, tempfile, threading, time
from pathlib import Path
from types import SimpleNamespace
from unittest.mock import patch
from datetime import datetime, timedelta
if __package__ in (None, ''):
    sys.path.insert(0, str(Path(__file__).resolve().parents[1]))
from anclicker.platform.qt_compat.QtWidgets import QApplication, QWidget
from anclicker.platform.qt_compat.QtCore import QDateTime
from anclicker.storage.database import DatabaseOperation
from anclicker.storage.graph_repository import GraphRepository
from anclicker.domain.instructions import InstructionDraft, ExecutionContext
from anclicker.execution.engine import ExecutionEngine
from anclicker.execution.services import ExecutionServices
from anclicker.app.scheduled_tasks import TaskScheduler
from anclicker.ui.scheduled_tasks_ui import ScheduleDialog
from anclicker.platform.rpa_bridge import get_bridge
from openpyxl import Workbook
from anclicker.ui.theme import THEMES

os.environ.setdefault('QT_QPA_PLATFORM', 'offscreen')
app = QApplication.instance() or QApplication([])
def until(predicate, seconds=5):
    deadline = time.monotonic() + seconds
    while time.monotonic() < deadline:
        app.processEvents()
        if predicate(): return
        time.sleep(.01)
    raise AssertionError('Timed out waiting for worker state')

class Main:
    def __init__(self, engine, target):
        self.engine = engine
        self.pause_calls = []
        self.thread = threading.Thread(target=target)
    def __getattr__(self, name): return getattr(self.engine, name)
    def isRunning(self): return self.thread.is_alive()
    def pause_for_schedule(self, enabled):
        self.pause_calls.append(enabled)
        self.engine.pause_for_schedule(enabled)

with tempfile.TemporaryDirectory() as folder:
    folder = Path(folder)
    cases = [(mode, manual, 'complete') for mode in (True, False) for manual in (False, True)]
    cases += [(mode, False, outcome) for mode in (True, False) for outcome in ('cancel', 'fail')]
    for mode, manual, outcome in cases:
        case = str(mode) + '-' + str(manual) + '-' + outcome
        db = DatabaseOperation(str(folder / (case + '.db')))
        project_db = DatabaseOperation(str(folder / (case + '-project.db')))
        repo = GraphRepository(project_db.db_path)
        repo.append_recording([InstructionDraft('时间等待', {'时长': 0}, note='scheduled')])
        book = Workbook(); repo.export_to_workbook(book, project_db)
        filename = folder / (case + '.xlsx'); book.save(filename); book.close()
        db.set_setting_value('当前文件路径', str(filename))
        main_repo = GraphRepository(db.db_path)
        main_repo.append_recording([InstructionDraft('时间等待', {'时长': 0}, note='main')])
        counters = {'main': 0, 'scheduled': 0}
        bridges = {}; release = threading.Event(); errors = []; logs = []
        def probe(context, command):
            label = command.note
            bridges[label] = get_bridge()
            if label == 'scheduled': context.variables['scheduled_only'] = 'isolated'
            while not (label == 'scheduled' and release.is_set()):
                if not context.runtime.wait(.01, context): return
                counters[label] += 1
            if label == 'scheduled' and outcome == 'fail':
                raise RuntimeError('synthetic scheduled failure')
        services = {'时间等待': probe}
        engine = ExecutionEngine(ExecutionServices(db, output=logs.append))
        context = ExecutionContext(services=services, output=logs.append)
        def main_run():
            try: engine.execute(main_repo.execution_snapshot(), context)
            except Exception as exc: errors.append(exc)
        window = QWidget(); window.db = db; window.execution_services = services
        window.view_workspace = SimpleNamespace(theme_mode='light', THEMES=THEMES)
        window.statusBar = SimpleNamespace(showMessage=lambda *a: None)
        window.send_message = logs.append; window._sync_stop_shortcut = lambda: None
        window.command_thread = Main(engine, main_run)
        scheduler = TaskScheduler(window); window.task_scheduler = scheduler; scheduler.timer.stop()
        window.command_thread.thread.start()
        try:
            until(lambda: counters['main'] >= 2)
            if manual:
                engine.pause(); time.sleep(.04)
            values = dict(path=str(filename), repeat='仅一次', next_run=(datetime.now()+timedelta(minutes=5)).isoformat(), pause_main=mode)
            task_id = scheduler.add(values)
            assert scheduler.task_by_id(task_id)['pause_main'] is mode
            dialog = ScheduleDialog(scheduler)
            dialog.load_task(task_id, editable=True)
            assert dialog.main_policy.currentData() is mode
            assert [dialog.main_policy.itemText(i) for i in range(2)] == ['暂停主任务(结束后恢复)', '定时任务不影响主任务运行']
            # Real save/load preserves the choice.
            dialog.save_task(True)
            assert scheduler.task_by_id(task_id)['pause_main'] is mode
            if not mode and not manual:
                dialog.show(); app.processEvents()
                output = Path('artifacts/validation/schedule-unaffected'); output.mkdir(parents=True, exist_ok=True)
                dialog.grab().save(str(output/'schedule-options.png'))
            dialog.close(); dialog.deleteLater()
            scheduler.task_by_id(task_id)['next_run'] = (datetime.now()-timedelta(seconds=1)).isoformat()
            with patch('anclicker.app.main_work.DatabaseOperation', return_value=db):
                scheduler.tick()
                until(lambda: (scheduler.tick() or counters['scheduled'] > 1))
                frozen = counters['main']; time.sleep(.1); app.processEvents()
                if mode or manual: assert counters['main'] == frozen, (mode, manual, counters)
                else: assert counters['main'] > frozen
                assert scheduler.blocks_main_start is mode
                assert ('scheduled_only' not in context.variables)
                assert (bridges['main'] is bridges['scheduled']) is mode
                if outcome == 'cancel': scheduler.stop()
                release.set()
                until(lambda: scheduler.worker is None and scheduler.active is None)
            scheduler.stop()  # Idle cleanup must not touch the main task either.
            assert window.command_thread.pause_calls == ([True, False] if mode else [])
            assert not engine.schedule_pause_requested
            assert engine.is_paused is manual
            if not manual:
                before = counters['main']; until(lambda: counters['main'] > before)
            if outcome == 'fail':
                assert 'synthetic scheduled failure' in scheduler.task_by_id(task_id)['status']
            elif outcome == 'cancel':
                assert '停止' in scheduler.task_by_id(task_id)['status']
            else:
                assert not any('执行失败' in message for message in logs), logs
            assert not errors, errors
            print('PASS schedule policy', mode, 'manual pause', manual, outcome, 'isolated variables/browser and cleanup', flush=True)
        finally:
            release.set(); scheduler.stop(); engine.request_stop()
            window.command_thread.thread.join(5)
            until(lambda: scheduler.worker is None)
            scheduler.timer.stop(); window.close(); app.processEvents()
    # Missing setting is backward compatible and defaults to pause.
    values.pop('pause_main')
    values['next_run'] = (datetime.now()+timedelta(minutes=5)).isoformat()
    assert scheduler._validate_task(values)['pause_main'] is True
print('PASS scheduling modes, persisted UI choice, old settings, manual pause and independent runtime resources')
