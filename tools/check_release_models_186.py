import sys,json,hashlib
from pathlib import Path
sys.path.insert(0,str(Path(__file__).resolve().parents[1]))
from models.draft_planner import plan_drafts
from models.agent_provider import AgentSettings
from models.dual_model import stop_dual,configuration
from anclicker.domain.instructions import ExecutionContext
ROOT=Path(__file__).resolve().parents[1]
recommended=json.loads((ROOT/'models/recommended_dual_model.json').read_text())
status=json.loads((ROOT/'models'/recommended['report']).read_text())
assert recommended['verified'] and status['verified']
config=configuration()
records={}
for role in ('splitter','converter'):
 assert config[role]==recommended[role]
 path=ROOT/'models'/recommended[role]
 with path.open('rb') as f:
  h=hashlib.sha256()
  for chunk in iter(lambda:f.read(1024*1024),b''):h.update(chunk)
 assert h.hexdigest()==status['model_hashes'][role]
 records[role]={'file':path.name,'sha256':h.hexdigest(),'bytes':path.stat().st_size}
print('PASS exact v6.5 model hashes',flush=True)
cases=[('帮我输入“测试通过”，先别按回车','文本输入'),('等待三秒','时间等待')]
results=[]
try:
 for prompt,expected in cases:
  context=ExecutionContext()
  result=plan_drafts(prompt,AgentSettings(),context)
  items=result['arguments']['instructions']
  assert len(items)==1 and items[0]['type_id']==expected,result
  trace=context.metadata['dual_model_trace']
  assert {t['role'] for t in trace}=={'splitter','converter'},trace
  assert all('v6_5' in t['model'] for t in trace),trace
  results.append({'prompt':prompt,'result':result,'trace':trace})
  print('PASS live inference: '+expected,flush=True)
finally:stop_dual()
(ROOT/'artifacts/validation/v1.8.6/models.json').write_text(json.dumps({'models':records,'live_checks':results,'prior_validation':status},ensure_ascii=False,indent=2),encoding='utf8')
