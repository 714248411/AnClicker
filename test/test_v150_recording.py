from types import SimpleNamespace
from instructions.models import InstructionDraft, CommandRecord, ExecutionContext
from recording_continuation import finish_continuation
from instructions.registry import get_instruction_spec
from unittest.mock import patch
import pytest


def test_continuation_inserts_below_selection_and_preserves_suffix():
    original=[InstructionDraft('文本输入',{'内容':str(i)}) for i in range(3)]
    new=[InstructionDraft('文本输入',{'内容':'new'})]
    view=SimpleNamespace(_continuation=(original,1))
    finish_continuation(view,new)
    assert [x.parameters['内容'] for x in view.drafts]==['0','new','1','2']
    assert view._continuation is None


def test_web_continuation_omits_setup_open_but_keeps_waits():
    original=[InstructionDraft('打开网页',{'url':'https://example.com'})]
    view=SimpleNamespace(_continuation=(original,1))
    recorded=[InstructionDraft('打开网页',{}),InstructionDraft('等待（秒）',{'seconds':2}),InstructionDraft('点击元素',{'selector':'#next'})]
    finish_continuation(view,recorded,web=True)
    assert [x.type_id for x in view.drafts]==['打开网页','等待（秒）','点击元素']
    assert view.drafts[1].parameters['seconds']==2


def test_cancelled_continuation_retains_original():
    original=[InstructionDraft('文本输入',{'内容':'keep'})]
    view=SimpleNamespace(_continuation=(original,1))
    finish_continuation(view,[])
    assert view.drafts==original


def test_multiple_points_order_offset_and_original_parameters():
    executor=get_instruction_spec('多坐标点击').create_executor()
    command=CommandRecord(None,'多坐标点击',{'坐标列表':'10,20;30,40','间隔':0,'随机偏移':'启用','水平偏移':3,'垂直偏移':2})
    with patch('instructions.common.actions.mouse_action') as click, patch('random.randint',side_effect=[-3,2,3,-2]):
        executor.execute(ExecutionContext(),command)
    assert [(x.args[1],x.args[2]) for x in click.call_args_list]==[(7,22),(33,38)]
    assert command.parameters['坐标列表']=='10,20;30,40'


def test_multiple_points_default_no_offset_and_stop():
    executor=get_instruction_spec('多坐标点击').create_executor()
    context=ExecutionContext()
    command=CommandRecord(None,'多坐标点击',{'坐标列表':'10,20;30,40','间隔':0})
    def stop(*args,**kwargs): context.stop_requested=True
    with patch('instructions.common.actions.mouse_action',side_effect=stop) as click, patch('random.randint') as random:
        executor.execute(context,command)
    click.assert_called_once_with('左键单击',10,20,interval_=0.1)
    random.assert_not_called()
