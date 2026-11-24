import sys,json
from pathlib import Path
ROOT=Path(__file__).resolve().parents[1];sys.path.insert(0,str(ROOT))
from models.web_contracts import normalize_web_request
from models.dual_model import plan,stop_dual
from models.agent_provider import AgentSettings
from anclicker.domain.instructions import ExecutionContext
for text in ['输入“hao123.com”','搜索hao123.com','打开文件“report.com”','发给 user@example.com']:
 assert normalize_web_request(text)==text,(text,normalize_web_request(text))
assert normalize_web_request('hao123.com')=='打开网页 https://hao123.com'
assert normalize_web_request('.com')=='.com'
cases=[('hao123.com','https://hao123.com',1),('www.hao123.com','https://www.hao123.com',1),('HAO123.COM','https://HAO123.COM',1),('hao123.com，，其中搜索123123','https://hao123.com',2)]
rows=[]
try:
 for text,url,count in cases:
  ctx=ExecutionContext();response=plan(text,AgentSettings(local_profile='cpu'),ctx)
  items=response.get('arguments',{}).get('instructions',[])
  passed=len(items)==count and items[0]['type_id']=='打开网页' and items[0]['parameters']['url']==url
  if count==2:passed=passed and items[1]['parameters'].get('text')=='123123' and items[1]['parameters'].get('pressEnter')=='是'
  rows.append({'request':text,'passed':passed,'response':response,'trace':ctx.metadata});print(text,passed,flush=True)
finally:stop_dual()
(ROOT/'artifacts/debug/domain-shorthand-results.json').write_text(json.dumps(rows,ensure_ascii=False,indent=2),encoding='utf8')
assert all(r['passed'] for r in rows)
