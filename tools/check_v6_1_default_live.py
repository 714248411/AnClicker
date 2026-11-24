import json
from models.draft_planner import plan_drafts
from models.agent_provider import AgentSettings
from models.dual_model import stop_dual
from anclicker.domain.instructions import ExecutionContext
ctx=ExecutionContext()
try:
 r=plan_drafts('帮我输入“测试通过”，先别按回车',AgentSettings(),ctx)
 assert r['arguments']['instructions'][0]['type_id']=='文本输入' and len(r['arguments']['instructions'])==1
 assert all('v6_1' in x['model'] for x in ctx.metadata['dual_model_trace'])
 print(json.dumps({'response':r,'models':[x['model'] for x in ctx.metadata['dual_model_trace']]},ensure_ascii=False))
finally:stop_dual()
