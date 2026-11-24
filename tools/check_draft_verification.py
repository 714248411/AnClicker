"""Acceptance state transitions: no early draft writes or repeated execution."""
import sys
from pathlib import Path
from unittest.mock import patch,Mock
if __package__ in (None,''):
    sys.path.insert(0,str(Path(__file__).resolve().parents[1]))
from models.agent_provider import AgentSettings
from models.draft_verification import verify_plan,judge_ocr
from anclicker.domain.instructions import ExecutionContext
from anclicker.execution.agent_runtime import AgentSession
steps=[{'type_id':'时间等待','parameters':{'时长':0}}, {'type_id':'截图OCR核验','parameters':{'预期文字':'成功','区域':'0,0,100,100'}}]
plan={'type':'tool_call','name':'draft_append_batch','arguments':{'instructions':steps}}
evidence={'verified':True,'text':'操作成功','missing':[],'screenshot':'test.png'}
def run(passed=True,ocr=True):
 session=AgentSession();events=[];executor=Mock();executor.execute.return_value=None
 with patch('models.draft_planner.plan_drafts',return_value=plan),patch('models.draft_verification.get_instruction_spec') as spec,patch('models.draft_verification.verify_screen',return_value={**evidence,'verified':ocr}),patch('models.draft_verification.judge_ocr',return_value={'passed':passed,'reason':'文字证据'}) as judge:
  spec.return_value.create_executor.return_value=executor
  session.run('完成操作，检查成功文字',AgentSettings(),ExecutionContext(),lambda *a:events.append(a))
  assert executor.execute.call_count==1
  if not ocr:judge.assert_not_called()
 return session,events
s,e=run();assert len(s.drafts)==1 and s.drafts[0].type_id=='时间等待' and not s.pending_verification
for model,ocr in [(False,True),(True,False)]:
 s,e=run(model,ocr);assert not s.drafts and e[-1][0]=='verification_failed'
 token=s.pending_verification['id'];s.resolve_verification(token,True,ExecutionContext())
 assert len(s.drafts)==1 and '[核验失败]' in s.drafts[0].note
 try:s.resolve_verification(token,True,ExecutionContext())
 except ValueError:pass
 else:raise AssertionError('duplicate acceptance')
s,e=run(False);s.resolve_verification(s.pending_verification['id'],False,ExecutionContext());assert not s.drafts
with patch('models.draft_verification.get_instruction_spec') as spec:
 outcome=verify_plan('等待',[steps[0]],AgentSettings(),ExecutionContext(),lambda *a:None)
 assert not outcome['passed'];spec.assert_not_called()
with patch('models.draft_verification.get_instruction_spec') as spec:
 outcome=verify_plan('等待',list(reversed(steps)),AgentSettings(),ExecutionContext(),lambda *a:None)
 assert not outcome['passed'];spec.assert_not_called()
with patch('models.draft_verification.verify_screen',side_effect=InterruptedError),patch('models.draft_verification.get_instruction_spec'):
 try:verify_plan('目标',steps,AgentSettings(),ExecutionContext(),lambda *a:None)
 except InterruptedError:pass
 else:raise AssertionError('cancel swallowed')
with patch('models.draft_verification.stop_local_model'),patch('models.draft_verification.request_json',return_value={'choices':[{'message':{'content':'{"passed":true,"reason":"文字符合"}'}}]}) as request:
 result=judge_ocr('目标',[evidence],AgentSettings(endpoint='https://example.com/v1'),ExecutionContext())
 assert result['passed'];payload=request.call_args.args[1]
 assert all(isinstance(m['content'],str) for m in payload['messages']) and 'image_url' not in str(payload)
print('PASS: OCR text-only judgment, success commit, failure/reject, no duplicate execution, cancellation, missing/stale evidence')
