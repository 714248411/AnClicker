import sys,json,subprocess
from pathlib import Path
from unittest.mock import patch
ROOT=Path(__file__).resolve().parents[1];sys.path.insert(0,str(ROOT))
from models.desktop_shell import recycle_bin_instruction,operate_recycle_bin
from models.draft_planner import plan_drafts
from models.agent_provider import AgentSettings
from anclicker.domain.instructions import ExecutionContext,CommandRecord
from anclicker.domain.agent_protocol import make_draft
from anclicker.instructions.registry import get_instruction_spec
for request in ['点击桌面回收站','单击桌面上的回收站','请帮我点一下桌面的“回收站”图标','选中回收站']:
 with patch('models.draft_planner._dual.load',side_effect=AssertionError('must not guess a path')):
  response=plan_drafts(request,AgentSettings(),ExecutionContext())
 item=response['arguments']['instructions'][0]
 assert item['type_id']=='运行Python' and "('select')" in item['parameters']['代码']
 ctx=ExecutionContext();draft=make_draft(**item)
 with patch('models.desktop_shell.subprocess.run',return_value=subprocess.CompletedProcess([],0,json.dumps({'selected':True,'target':'回收站'}),'')) as call:
  result=get_instruction_spec(draft.type_id).create_executor().execute(ctx,CommandRecord(None,draft.type_id,draft.parameters))
  assert result['selected'] and ctx.variables['桌面操作结果']['selected']
  assert '-File' in call.call_args.args[0] and call.call_args.kwargs['timeout']==20
for request in ['打开回收站','双击桌面回收站']:
 assert "('open')" in recycle_bin_instruction(request)['parameters']['代码']
for request in ['不要点击桌面回收站','清空回收站','点击网页回收站','点击桌面回收站然后删除文件','如果存在就点击回收站','点击桌面文件夹']:
 assert recycle_bin_instruction(request) is None,request
with patch('models.desktop_shell.os.startfile') as launch:
 assert operate_recycle_bin('open')['status']=='requested'
 launch.assert_called_once_with('shell:RecycleBinFolder')
for output in [subprocess.CompletedProcess([],1,'','not found'),subprocess.CompletedProcess([],0,'{}',''),subprocess.CompletedProcess([],0,'invalid','')]:
 with patch('models.desktop_shell.subprocess.run',return_value=output):
  try:operate_recycle_bin('select')
  except RuntimeError:pass
  else:raise AssertionError('unverified selection accepted')
print('PASS recycle bin routing, select/open distinction, internal Python return binding, missing-target errors and negation; desktop actions mocked')
