import json,sys
from pathlib import Path
ROOT=Path.cwd();sys.path.insert(0,str(ROOT))
from models.draft_planner import plan_drafts
from models.dual_model import stop_dual,configuration
from models.agent_provider import AgentSettings
from anclicker.domain.instructions import ExecutionContext
case=json.loads((ROOT/'artifacts/debug/multi-task-v6_5/v6_5/results.json').read_text(encoding='utf8'))['cases'][6]
ctx=ExecutionContext()
try:
 response=plan_drafts(case['request'],AgentSettings(local_profile='cpu'),ctx)
 assert [x['type_id'] for x in response['arguments']['instructions']]==case['types']
 assert all('v6_5' in t['model'] for t in ctx.metadata['dual_model_trace'])
 (ROOT/'models/anclicker-v6_5/default-entry-smoke.json').write_text(json.dumps({'passed':True,'configuration':configuration(),'request':case['request'],'response':response,'trace':ctx.metadata['dual_model_trace']},ensure_ascii=False,indent=2),encoding='utf8')
 print('DEFAULT_V6_5_SIX_ACTIONS_PASS',flush=True)
finally:stop_dual()
