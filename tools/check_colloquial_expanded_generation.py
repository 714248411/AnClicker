import sys,json,time
from pathlib import Path
ROOT=Path(__file__).resolve().parents[1];sys.path.insert(0,str(ROOT))
from models.draft_planner import plan_drafts
from models.agent_provider import AgentSettings
from models.dual_model import stop_dual
from anclicker.domain.instructions import ExecutionContext
OUT=ROOT/'artifacts/debug/colloquial-expanded';cases=json.loads((OUT/'generation-cases.json').read_text(encoding='utf8'));rows=[]
from tools.colloquial_expanded_judge import judge

try:
 for n,case in enumerate(cases,1):
  ctx=ExecutionContext();start=time.monotonic()
  try:r=plan_drafts(case['text'],AgentSettings(local_profile='cpu'),ctx);errors=judge(case,r);row={**case,'response':r,'errors':errors,'passed':not errors}
  except Exception as e:row={**case,'passed':False,'error':str(e)}
  row.update(elapsed_seconds=round(time.monotonic()-start,2),trace=ctx.metadata);rows.append(row)
  (OUT/'generation-results.json').write_text(json.dumps(rows,ensure_ascii=False,indent=2),encoding='utf8')
  print(n,len(cases),row['passed'],case['text'],row.get('errors',row.get('error')),flush=True)
finally:stop_dual()
print('COMPLETED',sum(r['passed'] for r in rows),len(rows),flush=True)
