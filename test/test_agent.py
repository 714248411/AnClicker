import json,time,threading
from unittest.mock import patch
import pytest
from agent_protocol import *
from agent_provider import AgentSettings,ModelClient
from agent_runtime import AgentSession
from instructions.models import ExecutionContext


def test_catalog_includes_every_palette_instruction():
    entries=catalog()
    assert len(entries)==len(list(iter_instruction_specs()))
    for entry in entries:
        schema=instruction_schema(entry['type_id'])
        assert schema['type_id']==entry['type_id']
        assert schema['parameters']['additionalProperties'] is False
    assert any(e['type_id']=='后台答题器' for e in catalog('Word'))

@pytest.mark.parametrize('name,args',[
 ('exec',{}),('browser',{'action':'click'}),('browser',{'action':'view','text':'x'}),
 ('draft_append',{'type_id':'时间等待','parameters':{},'repeat_count':True}),
 ('browser',{'action':'scroll','direction':'left'}),('draft_read',{'extra':1})])
def test_reject_malformed_tools(name,args):
    with pytest.raises((ValueError,TypeError)):validate_call(name,args)

def test_instruction_draft_defaults_bounds_and_update():
    session=AgentSession(bridge=object());ctx=ExecutionContext()
    session.execute('draft_append',{'type_id':'移动鼠标','parameters':{'类型':'指定坐标','坐标':'12,34'}},ctx)
    session.execute('draft_update',{'row':1,'parameters':{'坐标':'56,78'}},ctx)
    assert session.drafts[0].parameters['坐标']=='56,78'
    with pytest.raises(ValueError):session.execute('draft_update',{'row':1,'parameters':{'距离':-10}},ctx)
    assert session.drafts[0].parameters['坐标']=='56,78'
    with pytest.raises(ValueError):make_draft('时间等待',{'随便编的参数':1})
    assert export_drafts(session.drafts)['protocol']==VERSION

@pytest.mark.parametrize('backend',['compatible','ollama'])
@pytest.mark.parametrize('mode',['json','native'])
def test_provider_protocol_roundtrip(backend,mode):
    cfg=AgentSettings(backend=backend,mode=mode)
    call={'type':'function','id':'call_1','function':{'name':'instructions_search','arguments':{'query':'等待'}}}
    if backend=='compatible':call['function']['arguments']=json.dumps(call['function']['arguments'])
    msg={'role':'assistant','tool_calls':[call]}
    if mode=='json':msg={'content':json.dumps({'type':'tool_call','name':'instructions_search','arguments':{'query':'等待'}})}
    data={'message':msg} if backend=='ollama' else {'choices':[{'message':msg,'finish_reason':'stop'}]}
    with patch('agent_provider.request_json',return_value=data) as request:
        client=ModelClient(cfg);response=client.chat([{'role':'user','content':'找等待'}],ExecutionContext())
    assert response['call']['arguments']=={'query':'等待'}
    assert request.call_args.args[1]['stream'] is False
    result=client.tool_message(response['call'],envelope('instructions_search',[]))
    if mode=='native' and backend=='compatible':assert result['tool_call_id']=='call_1'
    assert VERSION in result['content']

def test_stop_before_any_side_effect():
    class Bridge:
        def execute(self,*a,**k):pytest.fail('must not execute after stop')
    session=AgentSession(Bridge())
    with pytest.raises(InterruptedError):session.execute('browser',{'action':'open','url':'https://example.com'},ExecutionContext(stop_requested=True))

def test_run_reports_tool_error_without_false_success():
    cfg=AgentSettings(max_steps=2);events=[]
    call={'name':'draft_update','arguments':{'row':9,'parameters':{}},'id':''}
    responses=[{'message':{'role':'assistant','content':'{}'},'text':'','call':call},
               {'message':{'role':'assistant','content':'无法更新'},'text':'无法更新','call':None}]
    with patch.object(ModelClient,'chat',side_effect=responses):AgentSession(object()).run('修改第9行',cfg,ExecutionContext(),lambda *e:events.append(e))
    assert next(v for k,v in events if k=='tool_result')['ok'] is False
    assert events[-1]==('assistant','无法更新')

def test_request_cancel_is_prompt_and_never_dispatches():
    from agent_provider import request_json
    context=ExecutionContext()
    def slow(*a,**k):time.sleep(.5);raise RuntimeError('late')
    threading.Timer(.05,lambda:setattr(context,'stop_requested',True)).start()
    with patch('agent_provider.requests.Session.request',side_effect=slow):
        start=time.monotonic()
        with pytest.raises(InterruptedError):request_json('http://127.0.0.1',{},AgentSettings(),context)
        assert time.monotonic()-start<.4

def test_low_memory_selects_gpu_and_keeps_cpu_fallback(tmp_path,monkeypatch):
    from agent_local import launch_plans
    from types import SimpleNamespace
    monkeypatch.setattr('agent_local.Path.is_file',lambda *_:True)
    monkeypatch.setattr('agent_local.psutil.virtual_memory',lambda:SimpleNamespace(available=500*1024**2))
    plans=launch_plans(tmp_path,'auto',True)
    assert plans[0][2].startswith('GPU') and plans[1][2].startswith('CPU')
    assert launch_plans(tmp_path,'cpu',True)[0][2].startswith('CPU')
    assert launch_plans(tmp_path,'gpu',False)[0][2].startswith('CPU')

@pytest.fixture(autouse=True)
def isolate_local_service(monkeypatch):
    from contextlib import nullcontext
    monkeypatch.setattr('agent_local.local_model_lease',lambda *args:nullcontext())


def test_stop_during_browser_start_does_not_send_command():
    from instructions.common.rpa_bridge import RpaBridge
    context=ExecutionContext();bridge=RpaBridge('stop-test')
    with patch.object(bridge,'_start',side_effect=lambda:setattr(context,'stop_requested',True)),patch.object(bridge,'close') as close:
        with pytest.raises(InterruptedError):bridge.execute({'id':'openUrl'},context=context)
        close.assert_called_once()
        assert bridge.sequence==0


def test_compatible_missing_call_id_is_rejected_before_dispatch():
    response={'choices':[{'message':{'tool_calls':[{'function':{'name':'draft_read','arguments':'{}'}}]}}]}
    with patch('agent_provider.request_json',return_value=response):
        with pytest.raises(ValueError,match='tool_call_id'):ModelClient(AgentSettings(mode='native')).chat([],ExecutionContext())
