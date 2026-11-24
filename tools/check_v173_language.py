import sys,os,json,time,importlib.util
from pathlib import Path
WORK=Path(__file__).resolve().parents[1];OUT=WORK/'artifacts/debug/v173-retest';label=sys.argv[1]
ROOT=(OUT/'source/AnClicker-v1.7.3') if label=='release' else WORK
if label=='release':os.environ['ANCLICKER_AGENT_HOME']=str(OUT/'release-runtime')
os.environ['ANCLICKER_DATA_DIR']=str(OUT/(label+'-data'))
sys.path.insert(0,str(ROOT))
from info import CURRENT_VERSION
from models.draft_planner import plan_drafts
from models.agent_provider import AgentSettings
from models.dual_model import stop_dual,configuration
from anclicker.domain.instructions import ExecutionContext
assert CURRENT_VERSION=='v1.7.3',CURRENT_VERSION
for name in ['models.draft_planner','models.dual_model','anclicker.domain.instructions']:
 assert Path(sys.modules[name].__file__).resolve().is_relative_to(ROOT.resolve()),name
spec=importlib.util.spec_from_file_location('external_test_judge',WORK/'tools/colloquial_expanded_judge.py');judge=importlib.util.module_from_spec(spec);spec.loader.exec_module(judge)
cases=[]
for filename,group in [('generation-cases.json','original24'),('heldout-cases.json','new12')]:
 cases.extend({**c,'test_group':group} for c in json.loads((WORK/'artifacts/debug/correction-memory'/filename).read_text(encoding='utf8')))
rows=[]
try:
 for i,c in enumerate(cases,1):
  ctx=ExecutionContext();start=time.monotonic()
  try:
   response=plan_drafts(c['text'],AgentSettings(local_profile='cpu'),ctx);errors=judge.judge(c,response)
   if 'distance' in c and not any(x['parameters'].get('距离')==c['distance'] for x in response.get('arguments',{}).get('instructions',[])):errors.append('滚动格数不符')
   row={**c,'passed':not errors,'errors':errors,'response':response}
  except Exception as e:row={**c,'passed':False,'error':str(e)}
  row.update(elapsed_seconds=round(time.monotonic()-start,3),trace=ctx.metadata);rows.append(row)
  (OUT/(label+'-language.json')).write_text(json.dumps({'version':CURRENT_VERSION,'code_root':str(ROOT),'configuration':configuration(),'cases':rows},ensure_ascii=False,indent=2),encoding='utf8')
  print(label,i,len(cases),row['passed'],c['text'],row.get('errors',row.get('error')),flush=True)
finally:stop_dual()
print('COMPLETED',label,sum(r['passed'] for r in rows),len(rows),flush=True)
