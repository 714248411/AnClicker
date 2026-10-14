from types import SimpleNamespace
from unittest.mock import Mock
import pytest
from qt_compat.QtWidgets import QApplication
from execution_timing import *
from instructions.models import ExecutionContext, CommandRecord
from instructions.common import actions
from instructions.common.executor import InstructionExecutorBase

class Database:
    def __init__(self): self.values = {}
    def get_setting_value(self, key): return self.values.get(key)
    def update_settings(self, **values): self.values.update(values)


def context(**values):
    db = Database();db.values.update(values)
    return ExecutionContext(metadata={'database': db})


def test_advanced_dialog_saves_only_on_accept_and_defaults_zero():
    app = QApplication.instance() or QApplication([])
    db = Database()
    dialog = AdvancedTimingDialog(None, db)
    assert all(spin.value() == 0 for spin in dialog.spins.values())
    dialog.spins[IMAGE_DELAY].setValue(.123)
    dialog.reject();assert db.values == {}
    dialog = AdvancedTimingDialog(None, db)
    for spin in dialog.spins.values():spin.setValue(.007)
    dialog.accept()
    assert all(value == .007 for value in read_timing(db).values())
    dialog = AdvancedTimingDialog(None, db)
    assert all(spin.value() == .007 for spin in dialog.spins.values())
    dialog.close()


def test_delayed_match_is_refreshed_and_missing_target_never_clicked(monkeypatch):
    ctx=context(**{IMAGE_DELAY:.2})
    events=[]
    def wait(c, delay):events.append(('wait',delay));return True
    locate=Mock(side_effect=[SimpleNamespace(x=4,y=5),None])
    gui=Mock()
    monkeypatch.setattr(actions,'wait_interruptibly',wait)
    monkeypatch.setattr(actions,'locate_image',locate)
    monkeypatch.setattr(actions,'pyautogui_module',lambda:gui)
    assert actions.click_image({},ctx) is None
    assert events==[('wait',.2)]
    gui.click.assert_not_called();gui.moveTo.assert_not_called()


def test_custom_hold_multiclick_and_after_click_are_interruptible(monkeypatch):
    ctx=context(**{PRESS_DURATION:.02, CLICK_INTERVAL:.03, AFTER_CLICK:.04})
    waits=[];gui=Mock(FAILSAFE=True)
    monkeypatch.setattr(actions,'pyautogui_module',lambda:gui)
    monkeypatch.setattr(actions,'wait_interruptibly',lambda c,s: waits.append(s) or True)
    assert actions.mouse_action('左键双击',4,5,move_first=False,context=ctx)
    assert waits==[0,.02,.03,.02,.04]
    assert gui.mouseDown.call_count==gui.mouseUp.call_count==2
    gui.reset_mock();waits.clear()
    monkeypatch.setattr(actions,'wait_interruptibly',lambda c,s:s==0)
    assert actions.mouse_action('左键双击',4,5,move_first=False,context=ctx) is False
    assert gui.mouseDown.call_count==gui.mouseUp.call_count==1


def test_interval_only_between_actions_including_repeats(monkeypatch):
    ctx=context(**{COMMAND_INTERVAL:.12})
    events=[]
    class Executor(InstructionExecutorBase):
        def execute_once(self, context, command):events.append('action')
    monkeypatch.setattr(actions,'wait_interruptibly',lambda c,s:events.append(s) or True)
    executor=Executor()
    executor.execute(ctx,CommandRecord(1,'时间等待',{},repeat_count=3))
    assert events==['action',.12,'action',.12,'action']
    monkeypatch.setattr(actions,'wait_interruptibly',lambda c,s:False)
    executor.execute(ctx,CommandRecord(2,'时间等待',{}))
    assert events==['action',.12,'action',.12,'action']


def test_bad_values_cannot_create_infinite_wait():
    db=Database();db.values={IMAGE_DELAY:'nan',AFTER_CLICK:'inf',PRESS_DURATION:'bad',CLICK_INTERVAL:'-3',COMMAND_INTERVAL:'9000'}
    result=read_timing(db)
    assert all(result[k]==0 for k in (IMAGE_DELAY,AFTER_CLICK,PRESS_DURATION,CLICK_INTERVAL))
    assert result[COMMAND_INTERVAL]==3600
