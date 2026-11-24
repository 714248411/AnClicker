import sys,json,time
from pathlib import Path
ROOT=Path(__file__).resolve().parents[1];sys.path.insert(0,str(ROOT))
from models.dual_model import plan,stop_dual,configuration
from models.agent_provider import AgentSettings
from anclicker.domain.instructions import ExecutionContext
from models.training.evaluate_v6 import equivalent,step
wait=lambda n:step('时间等待',时长=n,单位='秒')
web=lambda u:step('打开网页',url=u)
type_text=lambda s:step('文本输入',内容=s)
search=lambda s:step('输入文本',selector="input[data-hook='searchInput']",by='CSS选择器',text=s,pressEnter='是',clear='是')
cases=[
('输入再见，然后等两秒',[type_text('再见'),wait(2)]),
('输入并列第一，再等三秒',[type_text('并列第一'),wait(3)]),
('输入会议结束后再联系，别回车，最后等一秒',[type_text('会议结束后再联系'),wait(1)]),
('先等两秒然后输入你好再等三秒',[wait(2),type_text('你好'),wait(3)]),
('输入周五，哦不，改成周六，然后等两秒',[type_text('周六'),wait(2)]),
('打开hao123.com，搜索北京天气，不对，改成上海天气，最后等三秒',[web('https://hao123.com'),search('上海天气'),wait(3)]),
('打开hao123.com，搜索“123123”，不要提交，然后等两秒',[web('https://hao123.com'),step('输入文本',selector="input[data-hook='searchInput']",by='CSS选择器',text='123123',pressEnter='否',clear='是'),wait(2)]),
('打开hao123.com，搜索123123，别回车，再等两秒',[web('https://hao123.com'),step('输入文本',selector="input[data-hook='searchInput']",by='CSS选择器',text='123123',pressEnter='否',clear='是'),wait(2)]),
('我想先打开hao123.com，然后在搜索框里输入天气，先别提交，最后等三秒',[web('https://hao123.com'),step('输入文本',selector="input[data-hook='searchInput']",by='CSS选择器',text='天气',pressEnter='否',clear='是'),wait(3)]),
('打开example.org，然后打开example.net，最后等两秒',[web('https://example.org'),web('https://example.net'),wait(2)]),
('输入“请等待，然后再试”，并且不要回车，然后等两秒',[type_text('请等待，然后再试'),wait(2)]),
('打开hao123.com，搜索天气，然后把那个关掉',None)]
version=sys.argv[sys.argv.index('--model-version')+1] if '--model-version' in sys.argv else 'v6_4'
config={'enabled':True,'splitter':f'anclicker-{version}-splitter-q4_0.gguf','converter':f'anclicker-{version}-converter-q4_0.gguf'} if '--candidate' in sys.argv else None
rows=[];label=sys.argv[1] if len(sys.argv)>1 else 'baseline'
try:
 for text,expected in cases:
  ctx=ExecutionContext();row={'request':text,'expected':expected,'passed':False}
  try:
   response=plan(text,AgentSettings(local_profile='cpu'),ctx,config=config);row['response']=response
   row['passed']=response.get('type')=='message' if expected is None else equivalent(response.get('arguments',{}).get('instructions',[]),expected)
  except Exception as e:row['error']=str(e)
  row['metadata']=ctx.metadata;rows.append(row);print(json.dumps({k:row.get(k) for k in ['request','passed','error']},ensure_ascii=False),flush=True)
  (ROOT/('artifacts/debug/long-sentence-v2-'+label+'.json')).write_text(json.dumps({'config':config or configuration(),'passed':sum(x['passed'] for x in rows),'total':len(cases),'completed':len(rows),'cases':rows},ensure_ascii=False,indent=2),encoding='utf8')
finally:stop_dual()
print('COMPLETE',sum(x['passed'] for x in rows),len(rows),flush=True)

if label!='baseline':assert all(x['passed'] for x in rows),'Long sentence regression failed'
