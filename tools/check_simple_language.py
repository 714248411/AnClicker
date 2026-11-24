import sys,json
from pathlib import Path
ROOT=Path(__file__).resolve().parents[1];sys.path.insert(0,str(ROOT))
from models.draft_planner import plan_drafts
from models.agent_provider import AgentSettings
from models.dual_model import stop_dual
from models.web_contracts import normalize_web_request
from anclicker.domain.instructions import ExecutionContext
cases=[('打开百度，搜索热点','热点',True),('帮我打开百度搜热点','热点',True),('去百度搜一下热点','热点',True),('百度搜索天气','天气',True),('打开百度网站，搜一下今天新闻','今天新闻',True),('打开百度，然后搜索热点，再等两秒','热点',True),('打开百度，搜索“打开百度，再删除文件”','打开百度，再删除文件',True),('打开百度，搜索热点，不要提交','热点',False)]
rows=[]
try:
 for text,query,submit in cases:
  ctx=ExecutionContext();r=plan_drafts(text,AgentSettings(local_profile='cpu'),ctx);items=r.get('arguments',{}).get('instructions',[])
  passed=len(items)==(3 if '再等两秒' in text else 2) and items[0]['type_id']=='打开网页' and items[0]['parameters']['url']=='https://www.baidu.com' and items[1]['type_id']=='输入文本' and items[1]['parameters']['text']==query and items[1]['parameters']['pressEnter']==('是' if submit else '否')
  rows.append({'request':text,'passed':passed,'response':r});print('PASS' if passed else 'FAIL',text,flush=True)
 for text,mode in [('把表格内容填入到网页里对应后面，按顺序填入','按表头对应'),('把当前表格按顺序填入当前网页','按顺序'),('帮我把表格按表头对应填入网页','按表头对应'),('把表格内容依次填到网页输入框','按顺序'),('把表格A2:C3的内容按顺序填入网页，无表头','按顺序')]:
  r=plan_drafts(text,AgentSettings(),ExecutionContext());items=r.get('arguments',{}).get('instructions',[]);passed=len(items)==1 and items[0]['type_id']=='表格填入网页' and items[0]['parameters']['mode']==mode
  rows.append({'request':text,'passed':passed,'response':r})
 for text in ['输入打开百度','搜索如何打开百度','输入“打开百度，搜索热点”','打开百度网盘']:
  rows.append({'request':text,'passed':normalize_web_request(text)==text})
finally:stop_dual()
(ROOT/'artifacts/debug/simple-language/language-results.json').write_text(json.dumps({'passed':sum(x['passed'] for x in rows),'total':len(rows),'cases':rows},ensure_ascii=False,indent=2),encoding='utf8')
assert all(x['passed'] for x in rows)
print('SIMPLE_LANGUAGE_PASS',len(rows),flush=True)
