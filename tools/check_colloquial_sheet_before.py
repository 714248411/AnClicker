import sys,json
from pathlib import Path
ROOT=Path(__file__).resolve().parents[1];sys.path.insert(0,str(ROOT))
from models.draft_planner import plan_drafts
from models.agent_provider import AgentSettings
from anclicker.domain.instructions import ExecutionContext
rows=[]
for text in ['名字改成王五，编号别动','把这张表填到网页里，对着名字填','剩下的也照这个填','把网页上的结果放回刚才那张表']:
 try:r=plan_drafts(text,AgentSettings(),ExecutionContext())
 except Exception as e:r={'error':str(e)}
 rows.append({'request':text,'response':r});print(json.dumps(rows[-1],ensure_ascii=False),flush=True)
(ROOT/'artifacts/debug/colloquial-sheet/before.json').write_text(json.dumps(rows,ensure_ascii=False,indent=2),encoding='utf8')
