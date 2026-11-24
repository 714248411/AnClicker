"""Explicit planning-only diagnostics for source and frozen model pipelines."""
import json,time
from pathlib import Path

def run(args):
 from models.draft_planner import plan_drafts
 from models.agent_provider import AgentSettings
 from models.dual_model import stop_dual,configuration
 from anclicker.domain.instructions import ExecutionContext
 from info import CURRENT_VERSION
 source,target=map(Path,args)
 cases=json.loads(source.read_text(encoding='utf8'));rows=[]
 if not isinstance(cases,list) or not 1<=len(cases)<=200:raise ValueError('expected 1..200 cases')
 try:
  for case in cases:
   text=case['text'];ctx=ExecutionContext();start=time.monotonic()
   try:row={**case,'response':plan_drafts(text,AgentSettings(),ctx)}
   except Exception as error:row={**case,'error':str(error)}
   row.update(elapsed_seconds=round(time.monotonic()-start,3),trace=ctx.metadata);rows.append(row)
   target.write_text(json.dumps({'version':CURRENT_VERSION,'configuration':configuration(),'cases':rows},ensure_ascii=False,indent=2),encoding='utf8')
 finally:stop_dual()
 return 0 if all('error' not in r for r in rows) else 1
