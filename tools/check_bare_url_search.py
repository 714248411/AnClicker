import sys,json,time
from pathlib import Path
ROOT=Path(__file__).resolve().parents[1];sys.path.insert(0,str(ROOT))
from models.web_contracts import normalize_web_request
from models.dual_model import plan,stop_dual
from models.agent_provider import AgentSettings
from anclicker.domain.instructions import ExecutionContext
assert normalize_web_request('输入“hao123.com”')=='输入“hao123.com”'
assert normalize_web_request('打开 https://example.org')=='打开 https://example.org'
assert normalize_web_request('打开文件“report.txt”')=='打开文件“report.txt”'
assert normalize_web_request('打开网页，hao123.com，其中搜索123123')=='打开网页，https://hao123.com，其中搜索123123'
cases=[('我想打开网页，，hao123.com，，其中搜索123123','https://hao123.com','123123'),('打开 hao123.com，然后搜索“测试 空格”','https://hao123.com','测试 空格'),('访问网页，www.hao123.com，在里面搜一下123123','https://www.hao123.com','123123'),('打开网页，example.org', 'https://example.org',None),('打开网页',None,None)]
config={'enabled':True,'splitter':'anclicker-v6_1-splitter-q4_0.gguf','converter':'anclicker-v6_3-converter-q4_0.gguf'} if '--v6-3' in sys.argv else None
rows=[]
try:
 for text,url,query in cases:
  ctx=ExecutionContext();row={'request':text,'passed':False}
  try:
   response=plan(text,AgentSettings(local_profile='cpu'),ctx,config=config);row['response']=response
   if url is None:assert response['type']=='message'
   else:
    items=response['arguments']['instructions'];assert len(items)==(2 if query is not None else 1),items
    assert items[0]['type_id']=='打开网页' and items[0]['parameters']['url']==url,items
    if query is not None:
     assert items[1]['type_id']=='输入文本' and items[1]['parameters']['text']==query and items[1]['parameters']['pressEnter']=='是' and items[1]['parameters']['selector']=="input[data-hook='searchInput']",items
   row['passed']=True
  except Exception as e:row['error']=str(e)
  row['metadata']=ctx.metadata;rows.append(row);print(json.dumps(row,ensure_ascii=False),flush=True)
finally:stop_dual()
path=ROOT/('artifacts/debug/bare-url-search-v6_3-results.json' if config else 'artifacts/debug/bare-url-search-results.json');path.write_text(json.dumps(rows,ensure_ascii=False,indent=2),encoding='utf8')
assert all(x['passed'] for x in rows)
print('PASS',len(rows))
