"""Regression checks for atomic plans and the authenticated external-model API."""
import json
import threading
import sys
from pathlib import Path
from unittest.mock import patch
if __package__ in (None,''):
    sys.path.insert(0,str(Path(__file__).resolve().parents[1]))
import requests
from models.tool_api import ToolAPIServer
from models.agent_provider import AgentSettings
from anclicker.domain.instructions import ExecutionContext
from anclicker.execution.agent_runtime import AgentSession

def main():
    instructions=[{'type_id':'打开网页','parameters':{'url':'https://example.com'}},{'type_id':'时间等待','parameters':{'时长':2}}]
    session=AgentSession()
    response=session.execute('draft_append_batch',{'instructions':instructions},ExecutionContext())
    assert response['count']==2 and len(session.drafts)==2
    try:session.execute('draft_append_batch',{'instructions':[instructions[0],{'type_id':'不存在','parameters':{}}]},ExecutionContext())
    except (ValueError,KeyError):pass
    else:raise AssertionError('Invalid batch must fail')
    assert len(session.drafts)==2
    with patch('models.draft_planner.plan_drafts',return_value={'type':'tool_call','name':'browser','arguments':{'action':'open','url':'https://example.com'}}):
        try:session.run('test',AgentSettings(),ExecutionContext(),lambda *a:None)
        except ValueError:pass
        else:raise AssertionError('Draft mode executed a live action')
    with patch('models.draft_planner.plan_drafts',return_value={'type':'message','content':'请提供网址'}) as planner:
        session.run('打开网站后等待2秒',AgentSettings(),ExecutionContext(),lambda *a:None)
    with patch('models.draft_planner.plan_drafts',return_value={'type':'tool_call','name':'draft_append_batch','arguments':{'instructions':instructions}}) as planner:
        session.run('https://example.com',AgentSettings(),ExecutionContext(),lambda *a:None)
        assert '打开网站后等待2秒' in planner.call_args.args[0]
        assert 'https://example.com' in planner.call_args.args[0]
        assert session.pending_plan_text==''
    session.close()
    server=ToolAPIServer(('127.0.0.1',0),'test-secret')
    thread=threading.Thread(target=server.serve_forever,daemon=True);thread.start()
    url='http://127.0.0.1:'+str(server.server_port)
    client=requests.Session();client.trust_env=False
    try:
        assert client.get(url+'/v1/tools',timeout=5).status_code==401
        client.headers['Authorization']='Bearer test-secret'
        tools=client.get(url+'/v1/tools',timeout=5).json()['tools']
        assert 'draft_append_batch' in [x['function']['name'] for x in tools]
        assert 'browser' not in [x['function']['name'] for x in tools]
        sid=client.post(url+'/v1/sessions',json={},timeout=5).json()['session_id']
        body={'session_id':sid,'name':'draft_append_batch','arguments':{'instructions':instructions}}
        assert client.post(url+'/v1/tools/call',json=body,timeout=5).json()['ok']
        ast=client.post(url+'/v1/tools/call',json={'session_id':sid,'name':'workflow_read','arguments':{}},timeout=5).json()['result']
        patch_body={'session_id':sid,'name':'workflow_patch','arguments':{'base_revision':ast['revision'],'operations':[{'op':'update','target':ast['nodes'][1]['id'],'parameters':{'时长':5}}]}}
        assert client.post(url+'/v1/tools/call',json=patch_body,timeout=5).json()['ok']
        assert not client.post(url+'/v1/tools/call',json=patch_body,timeout=5).json()['ok']
        exported=client.post(url+'/v1/drafts/export',json={'session_id':sid},timeout=5).json()
        assert len(exported['instructions'])==2 and exported['kind']=='instruction_drafts'
        body['name']='browser';body['arguments']={'action':'open','url':'https://example.com'}
        assert client.post(url+'/v1/tools/call',json=body,timeout=5).status_code==400
        assert client.post(url+'/v1/sessions/close',json={'session_id':sid},timeout=5).json()['closed']
    finally:client.close();server.shutdown();server.server_close()
    print('PASS: atomic multi-step drafts, no partial writes, draft-only action guard, authenticated API and export')
if __name__=='__main__':main()
