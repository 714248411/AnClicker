"""Persistent local schedules, serialized with the interactive execution worker."""
import json
import uuid
import weakref
from datetime import datetime, timedelta
from pathlib import Path
from anclicker.platform.qt_compat.QtCore import QObject, QTimer, Signal
from anclicker.app.main_work import CommandThread
from anclicker.domain.instructions import ExecutionContext

from anclicker._imports import DeferredImports as _DeferredImports

# Dependencies declared here retain their existing on-demand loading boundaries.
_module_imports = _DeferredImports(globals(), {
    'release_execution_resources': ('from', 'anclicker.execution.actions', ('release_execution_resources',), 0),
    'application_state': ('from', 'anclicker.app.state', ('application_state',), 0),
    'ScheduleDialog': ('from', 'anclicker.ui.scheduled_tasks_ui', ('ScheduleDialog',), 0),
})


SETTING = '定时运行任务'

def next_occurrence(task, now):
    due = datetime.fromisoformat(task['next_run'])
    if task['repeat'] == '仅一次':
        return None
    if task['repeat'] == '自定义':
        step = timedelta(minutes=max(1, int(task.get('interval_minutes', 60))))
    else:
        step = timedelta(days=7 if task['repeat'] == '每周' else 1)
    if due <= now:
        due += step * (int((now - due) / step) + 1)
    if task['repeat'] == '工作日':
        while due.weekday() >= 5:
            due += timedelta(days=1)
    return due.isoformat(timespec='seconds')


class ScheduledWorker(CommandThread):
    completed = Signal(str, str)

    def __init__(self, window, task):
        super().__init__(window)
        self.task = dict(task)
        self.run_unconnected = True
        owner = weakref.ref(self)
        def persist(variables):
            worker = owner()
            if worker is not None:
                worker._persist_variables(variables)
        def handle_error(command, error):
            worker = owner()
            return worker._handle_command_error(command, error) if worker is not None else 'stop'
        self.engine._persist_variables = persist
        self.engine._handle_command_error = handle_error

    def _persist_variables(self, variables):
        # The visible project's database and variables belong to the main task.
        pass

    def _handle_command_error(self, command, error):
        if command.error_policy == '自动跳过':
            self.send_message.emit('定时任务跳过失败指令：' + str(error))
            return 'continue'
        raise RuntimeError(f'指令 {command.id} 执行失败：{error}') from error

    def run(self):
        release_execution_resources = _module_imports.load('release_execution_resources')
        context = ExecutionContext(variables={}, services=self.engine.services.command_services() or {},
            output=self.send_message.emit)
        self.engine._prepare_context(context)
        self._active_context = context
        error = ''
        try:
            if self._stop_requested:
                raise RuntimeError('任务已取消')
            self._run_project(self.task['path'], context)
            if self._stop_requested or context.stop_requested or not self.start_state:
                error = '任务已停止'
        except Exception as exc:
            error = str(exc) or type(exc).__name__
        finally:
            cleanup_error = release_execution_resources(context)
            if cleanup_error is not None and not error:
                error = '运行资源释放失败：' + str(cleanup_error)
            self._active_context = None
            self.completed.emit(self.task['id'], error)


class TaskScheduler(QObject):
    changed = Signal()

    def __init__(self, window):
        super().__init__(window)
        self.window = window
        self.tasks = []
        try:
            saved = json.loads(window.db.get_setting_value(SETTING) or '[]')
            for task in saved if isinstance(saved, list) else []:
                if not isinstance(task, dict) or not all(k in task for k in ('id','path','repeat','next_run')):
                    continue
                datetime.fromisoformat(task['next_run'])
                self.tasks.append(task)
        except (ValueError, TypeError):
            window.statusBar.showMessage('部分定时任务设置无效，请检查定时任务。', 5000)
        self.queue = []
        self.active = None
        self.worker = None
        self.timer = QTimer(self)
        self.timer.setInterval(500)
        self.timer.timeout.connect(self.tick)
        self.timer.start()
        self.dialog = None

    @property
    def busy(self):
        return self.active is not None or bool(self.queue)

    def save(self):
        self.window.db.set_setting_value(SETTING, json.dumps(self.tasks, ensure_ascii=False))
        self.changed.emit()

    def _validate_task(self, task):
        task = dict(task)
        path = Path(task['path']).expanduser().resolve()
        if path.suffix.lower() != '.xlsx' or not path.is_file():
            raise ValueError('请选择存在的 .xlsx 项目文件。')
        due = datetime.fromisoformat(task['next_run'])
        if task.get('enabled', True) and due <= datetime.now():
            raise ValueError('请选择未来的执行时间。')
        if task['repeat'] not in ('仅一次', '每天', '工作日', '每周', '自定义'):
            raise ValueError('不支持的重复方式。')
        if task['repeat'] == '工作日':
            due = datetime.fromisoformat(task['next_run'])
            while due.weekday() >= 5:
                due += timedelta(days=1)
            task['next_run'] = due.isoformat(timespec='seconds')
        if task['repeat'] == '自定义':
            task['interval_minutes'] = max(1, min(525600, int(task.get('interval_minutes', 60))))
        task['path'] = str(path)
        return task

    def task_by_id(self, task_id):
        task = next((item for item in self.tasks if item['id'] == task_id), None)
        if task is None:
            raise ValueError('该定时任务已不存在。')
        return task

    def add(self, task):
        task = self._validate_task(task)
        enabled = bool(task.get('enabled', True))
        task.update(id=uuid.uuid4().hex, enabled=enabled,
                    status='等待执行' if enabled else '未启用')
        self.tasks.append(task)
        self.save()
        return task['id']

    def update_task(self, task_id, changes):
        task = self.task_by_id(task_id)
        if self.active and self.active['id'] == task_id:
            raise ValueError('任务正在执行，请结束后再编辑。')
        updated = self._validate_task(dict(task, **changes))
        updated['id'] = task_id
        updated['status'] = '等待执行' if updated.get('enabled', True) else '未启用'
        # Discard the old queued occurrence after a schedule has been changed.
        self.queue[:] = [item for item in self.queue if item['id'] != task_id]
        task.clear()
        task.update(updated)
        self.save()
        return task_id

    def set_enabled(self, task_id, enabled):
        task = self.task_by_id(task_id)
        if bool(task.get('enabled', True)) == bool(enabled):
            return
        if enabled and datetime.fromisoformat(task['next_run']) <= datetime.now():
            following = next_occurrence(task, datetime.now())
            if following is None:
                raise ValueError('单次任务时间已过去，请右击任务选择“编辑”，设置未来时间。')
            task['next_run'] = following
        task['enabled'] = bool(enabled)
        if not enabled:
            self.queue[:] = [item for item in self.queue if item['id'] != task_id]
        if not (self.active and self.active['id'] == task_id):
            task['status'] = '等待执行' if enabled else '未启用'
        self.save()

    def remove_task(self, task_id):
        task = self.task_by_id(task_id)
        if self.active and self.active['id'] == task_id:
            raise ValueError('请先结束当前定时任务，再删除。')
        self.queue[:] = [item for item in self.queue if item['id'] != task_id]
        self.tasks.remove(task)
        self.save()

    def tick(self, now=None):
        if getattr(self.window, '_closing', False):
            return
        now = now or datetime.now()
        for task in self.tasks:
            if not task.get('enabled', True) or datetime.fromisoformat(task['next_run']) > now:
                continue
            # Consume the occurrence before starting; a slow task cannot be queued twice.
            if not any(t['id'] == task['id'] for t in self.queue) and not (self.active and self.active['id'] == task['id']):
                self.queue.append(dict(task))
                task['status'] = '等待安全暂停当前任务'
            following = next_occurrence(task, now)
            if following is None:
                task['enabled'] = False
            else:
                task['next_run'] = following
            self.save()
        if self.active is None and self.queue:
            view = self.window.view_workspace
            application_state = _module_imports.load('application_state')
            if application_state(self.window).is_busy(excluding=('schedule', 'execution')):
                return
            self.active = self.queue.pop(0)
            self.window.command_thread.pause_for_schedule(True)
        if self.active is None or self.worker is not None:
            return
        main = self.window.command_thread
        if main.isRunning() and not main.schedule_pause_ack.is_set():
            return
        self._set_status(self.active['id'], '正在运行')
        self.window.send_message('定时任务开始：' + self.active['path'])
        self.worker = ScheduledWorker(self.window, self.active)
        self.worker.send_message.connect(self.window.send_message)
        self.worker.completed.connect(self._result)
        self.worker.finished.connect(self._finished)
        self.window.escape_stop.setEnabled(True)
        self.worker.start()

    def _set_status(self, task_id, status):
        for task in self.tasks:
            if task['id'] == task_id:
                task['status'] = status
        self.save()

    def _result(self, task_id, error):
        self._set_status(task_id, ('执行失败：' + error) if error else '已完成')
        main = self.window.command_thread
        following = ('主任务保持手动暂停。' if main.is_paused else '继续原任务。') if main.isRunning() else ''
        self.window.send_message(('定时任务结束：' + error) if error else '定时任务完成。' + following)

    def _finished(self):
        worker = self.worker
        self.worker = None
        self.active = None
        if self.queue:
            QTimer.singleShot(0, self.tick)
        else:
            self.window.command_thread.pause_for_schedule(False)
        self.window.escape_stop.setEnabled(self.window.command_thread.isRunning() or bool(self.queue))
        if worker is not None:
            worker.deleteLater()
        self.changed.emit()

    def stop(self):
        for task in self.queue:
            self._set_status(task['id'], '已取消本次执行')
        self.queue.clear()
        if self.worker is not None:
            self.worker.request_stop()
        elif self.active is not None:
            self._set_status(self.active['id'], '已取消本次执行')
            self.active = None
        if self.worker is None:
            self.window.command_thread.pause_for_schedule(False)

    def show_settings(self):
        ScheduleDialog = _module_imports.load('ScheduleDialog')
        theme = self.window.view_workspace.theme_mode
        if self.dialog is not None and self.dialog.theme_mode != theme:
            self.dialog.hide()
            self.dialog.deleteLater()
            self.dialog = None
        if self.dialog is None:
            self.dialog = ScheduleDialog(self)
        self.dialog.refresh()
        self.dialog.show()
        self.dialog.raise_()
        self.dialog.activateWindow()
