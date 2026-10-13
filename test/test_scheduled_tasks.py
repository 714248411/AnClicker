from datetime import datetime, timedelta
from threading import Event
from unittest.mock import patch
import time
import pytest
from qt_compat.QtWidgets import QApplication
from qt_compat.QtTest import QTest
from test.test_hidden_stop import host, pump_until
from test.test_project_call import project, mark
from 数据库操作 import DatabaseOperation
from scheduled_tasks import TaskScheduler, next_occurrence


def due(scheduler, path, repeat='仅一次'):
    scheduler.add(dict(path=str(path), description='测试', repeat=repeat,
        next_run=(datetime.now()+timedelta(minutes=1)).isoformat(timespec='seconds')))
    scheduler.tasks[-1]['next_run']=(datetime.now()-timedelta(seconds=1)).isoformat(timespec='seconds')
    return scheduler.tasks[-1]


def test_schedule_due_queue_once_and_recurrence(host,tmp_path):
    s=host.task_scheduler;s.timer.stop()
    path=tmp_path/'task.xlsx';project(path,[mark('scheduled')])
    once=due(s,path);daily=due(s,path,'每天');weekly=due(s,path,'每周')
    with patch.object(host.view_workspace.recording_page.__class__, 'busy', new_callable=__import__('unittest.mock',fromlist=['PropertyMock']).PropertyMock,return_value=True):
        s.tick();s.tick()
    assert len(s.queue)==3
    assert not once['enabled']
    assert datetime.fromisoformat(daily['next_run'])>datetime.now()
    assert datetime.fromisoformat(weekly['next_run'])>datetime.now()+timedelta(days=6)
    s.stop()
    loaded=TaskScheduler(host);loaded.timer.stop()
    assert len(loaded.tasks)==3
    assert not loaded.tasks[0]['enabled']


@pytest.mark.parametrize('paused',[False,True])
def test_scheduled_project_pauses_and_resumes_without_mutating_main(host,tmp_path,paused):
    s=host.task_scheduler;s.timer.stop()
    path=tmp_path/'task.xlsx';project(path,[mark('scheduled')])
    task=due(s,path)
    entered=Event();scheduled=Event();finish_main=Event();order=[]
    def main_action(context,command):
        entered.set()
        while not finish_main.is_set() and not context.stop_requested:
            if not context.metadata['wait_interruptibly'](.01,context):break
        order.append('main ended')
    def child_action(context,command):
        assert host.command_thread.schedule_pause_ack.is_set()
        assert context.metadata['database'].db_path != host.db.db_path
        assert context.variables == {}
        scheduled.set();order.append('scheduled')
    host.execution_services={'悬停后点击':main_action,'文本输入':child_action}
    before=host.workspace.repository.snapshot()
    assert host.start();pump_until(entered.is_set)
    if paused:host.command_thread.pause()
    with patch('main_work.DatabaseOperation',side_effect=lambda path=None: DatabaseOperation(path) if path else host.db):
        s.tick()
        pump_until(host.command_thread.schedule_pause_ack.is_set)
        s.tick()
        pump_until(lambda: s.active is None)
    assert scheduled.is_set() and order == ['scheduled']
    assert host.command_thread.is_paused == paused
    assert host.workspace.repository.snapshot() == before
    assert task['status']=='已完成'
    finish_main.set();host.command_thread.resume()
    pump_until(lambda:not host.command_thread.isRunning())


def test_missing_scheduled_file_restores_main_pause_gate(host,tmp_path):
    s=host.task_scheduler;s.timer.stop()
    path=tmp_path/'task.xlsx';project(path,[mark('unused')]);task=due(s,path);path.unlink()
    with patch('main_work.DatabaseOperation',side_effect=lambda path=None: DatabaseOperation(path) if path else host.db):
        s.tick();pump_until(lambda:s.active is None)
    assert task['status'].startswith('执行失败')
    assert not host.command_thread.schedule_pause_requested


def test_stop_scheduled_worker_does_not_resume_stopped_main(host,tmp_path):
    s=host.task_scheduler;s.timer.stop()
    path=tmp_path/'task.xlsx';project(path,[mark('scheduled')]);task=due(s,path)
    started=Event()
    def child(context,command):
        started.set()
        while context.metadata['wait_interruptibly'](.01,context):pass
    host.execution_services={'文本输入':child}
    with patch('main_work.DatabaseOperation',side_effect=lambda path=None: DatabaseOperation(path) if path else host.db):
        s.tick();pump_until(started.is_set)
        host.global_shortcut_key('终止线程')
        pump_until(lambda:s.active is None)
    assert not s.busy
    assert not host.command_thread.schedule_pause_requested
    assert '停止' in task['status']


def test_alarm_opens_dialog_with_project_and_recurrence(host):
    host.task_scheduler.timer.stop()
    host.workspace.palette.schedule_button.click()
    dialog=host.task_scheduler.dialog
    assert dialog.isVisible()
    assert dialog.repeat.count()==5
    assert not dialog.advanced.isVisible()
    dialog.advanced_button.click()
    assert dialog.advanced.isVisible()
    dialog.reject()

def test_workdays_and_custom_interval_skip_missed_occurrences():
    friday=datetime(2026,10,16,9)
    task={'repeat':'工作日','next_run':friday.isoformat()}
    assert next_occurrence(task,friday)=='2026-10-19T09:00:00'
    task={'repeat':'自定义','next_run':friday.isoformat(),'interval_minutes':15}
    assert next_occurrence(task,friday+timedelta(hours=2,minutes=4))=='2026-10-16T11:15:00'


def test_two_due_projects_run_serially_and_keep_root_database(host,tmp_path):
    s=host.task_scheduler;s.timer.stop();log=[]
    for label in ('first','second'):
        path=tmp_path/(label+'.xlsx');project(path,[mark(label)]);due(s,path)
    host.execution_services={'文本输入':lambda context,command:log.append(command.parameters['内容'])}
    before=host.workspace.repository.snapshot()
    with patch('main_work.DatabaseOperation',side_effect=lambda path=None: DatabaseOperation(path) if path else host.db):
        s.tick();pump_until(lambda:not s.busy)
    assert log==['first','second']
    assert host.workspace.repository.snapshot()==before
    assert not host.command_thread.schedule_pause_requested


def test_schedule_waits_for_held_input_to_be_released(host):
    from instructions.models import ExecutionContext
    from threading import Thread
    t=host.command_thread
    t._active_context=ExecutionContext(metadata={'recorded_buttons':{'left'}})
    t.pause_for_schedule(True)
    assert t.check_mutex() # Don't interrupt a drag between press and release.
    assert not t.schedule_pause_ack.is_set()
    t._active_context.metadata['recorded_buttons'].clear()
    result=[]
    helper=Thread(target=lambda:result.append(t.check_mutex()))
    helper.start()
    assert t.schedule_pause_ack.wait(1)
    t.pause_for_schedule(False);helper.join(1)
    assert result==[True]


def test_schedule_ui_grab(host):
    host.task_scheduler.timer.stop()
    host.view_workspace.theme_mode='dark';host.view_workspace._apply_theme()
    host.task_scheduler.show_settings()
    dialog=host.task_scheduler.dialog
    QTest.qWait(50)
    dialog.grab().save('validation/schedule-settings-dark.png')
    assert dialog.grab().toImage().pixelColor(0,0).alpha()==0
    dialog.reject()

def test_active_schedule_blocks_updates_recording_and_parameter_execution(host):
    from instructions.models import InstructionDraft
    from instructions.registry import get_instruction_spec
    from qt_compat.QtCore import QObject, Signal
    host.task_scheduler.timer.stop()
    host.task_scheduler.active={'id':'pending','path':'unused'}
    assert not host.start()
    assert not host.prepare_for_update()[0]
    with pytest.raises(RuntimeError):host.workspace._check_parameter_save_allowed()
    class Editor(QObject):
        test_requested=Signal(object)
    editor=Editor(host)
    host.workspace._connect_editor_test(editor,get_instruction_spec('时间等待'))
    with patch.object(host.workspace,'_editor_context',side_effect=AssertionError('must not execute')):
        editor.test_requested.emit(InstructionDraft('时间等待',{}))
    host.task_scheduler.active=None
