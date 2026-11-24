"""Transactional patch correctness, stale revisions and Agent integration."""
import json
from copy import deepcopy
from unittest.mock import patch
from models.workflow_ast import from_drafts,to_drafts,apply_patch
from anclicker.domain.agent_protocol import make_draft
from anclicker.domain.instructions import ExecutionContext
from anclicker.execution.agent_runtime import AgentSession
from models.agent_provider import AgentSettings

def main():
    original=from_drafts([make_draft('时间等待',{'时长':n,'单位':'秒'}) for n in (1,2,3)])
    frozen=json.dumps(original,sort_keys=True)
    result=apply_patch(original,{'base_revision':0,'operations':[{'op':'update','target':'n2','parameters':{'时长':8}},{'op':'delete','target':'n1'},{'op':'add','after':'n2','node':{'type_id':'文本输入','parameters':{'内容':'新增'}}},{'op':'move','target':'n3','after':None}]})
    assert [n['id'] for n in result['nodes']]==['n3','n2','n4']
    assert result['nodes'][1]['parameters']['时长']==8 and result['nodes'][0]['parameters']['时长']==3
    assert json.dumps(original,sort_keys=True)==frozen and result['revision']==1
    assert len(to_drafts(result))==3
    invalid=[{'base_revision':9,'operations':[{'op':'delete','target':'n1'}]},
      {'base_revision':0,'operations':[{'op':'delete','target':'n1'},{'op':'update','target':'n1','parameters':{'时长':3}}]},
      {'base_revision':0,'operations':[{'op':'update','target':'n2','parameters':{'不存在':8}}]},
      {'base_revision':0,'operations':[{'op':'move','target':'n1','after':'n1'}]},
      {'base_revision':0,'operations':[{'op':'delete','target':'missing'}]}]
    for bad in invalid:
        try:apply_patch(original,bad)
        except ValueError:pass
        else:raise AssertionError('Bad patch accepted')
        assert json.dumps(original,sort_keys=True)==frozen
    session=AgentSession();session.drafts=to_drafts(original)
    request={'base_revision':0,'operations':[{'op':'delete','target':'n2'}]};events=[]
    with patch('models.draft_planner.plan_drafts',return_value={'type':'tool_call','name':'workflow_patch','arguments':request}):
        session.run('删除第2步',AgentSettings(),ExecutionContext(),lambda kind,value:events.append((kind,value)))
    assert len(session.drafts)==2 and any(kind=='drafts' for kind,_ in events)
    assert session.workflow_snapshot()['revision']==1
    session.drafts.reverse();assert session.workflow_snapshot()['revision']==2
    try:session.apply_workflow_patch(request)
    except ValueError:pass
    else:raise AssertionError('Stale patch accepted after UI edit')
    session.close()
    print('PASS patch add/delete/update/move, untouched fields, rollback, stale revisions and Agent draft integration')
if __name__=='__main__':main()
