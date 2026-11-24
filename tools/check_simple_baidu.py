import sys,json
from pathlib import Path
from unittest.mock import patch
ROOT=Path(__file__).resolve().parents[1];sys.path.insert(0,str(ROOT))
from models.draft_planner import plan_drafts
from models.agent_provider import AgentSettings
from models.dual_model import stop_dual
from anclicker.domain.instructions import ExecutionContext,CommandRecord
from anclicker.domain.agent_protocol import make_draft
from anclicker.instructions.registry import get_instruction_spec
from anclicker.platform.rpa_bridge import RpaBridge
ctx=ExecutionContext();bridge=RpaBridge('simple-baidu-acceptance');report={'request':'打开百度，搜索热点','passed':False}
try:
 response=plan_drafts(report['request'],AgentSettings(local_profile='cpu'),ctx);report['plan']=response
 items=response.get('arguments',{}).get('instructions',[])
 assert [x['type_id'] for x in items]==['打开网页','输入文本'],response
 assert items[0]['parameters']['url']=='https://www.baidu.com'
 assert items[1]['parameters']['text']=='热点' and items[1]['parameters']['pressEnter']=='是'
 with patch('anclicker.instructions.common.rpa_instruction.get_bridge',return_value=bridge):
  for item in items:
   d=make_draft(**item);get_instruction_spec(d.type_id).create_executor().execute(ctx,CommandRecord(None,d.type_id,d.parameters));print('EXECUTED',d.type_id,flush=True)
 import time
 time.sleep(2)
 report['diagnostic']=bridge.execute({'id':'diagnosePage','params':{}})['result']
 value=bridge.execute({'id':'getText','params':{'selector':'textarea#chat-textarea, input[name="wd"]','by':'CSS选择器','varName':'搜索框内容'}})['variables']['搜索框内容']
 body=bridge.execute({'id':'getText','params':{'selector':'body','by':'CSS选择器','varName':'页面文字'}})['variables']['页面文字']
 report['query']=value;report['body_excerpt']=body[:1200]
 from urllib.parse import urlsplit,parse_qs
 assert parse_qs(urlsplit(report['diagnostic']['url']).query).get('wd')==['热点'],report['diagnostic']
 assert value=='热点',value
 assert '百度安全验证' not in body,'百度触发验证，不能认定搜索成功'
 assert any(marker in body for marker in ['百度为您找到','相关搜索','搜索工具','百度热搜','搜索结果']),body[:300]
 report['passed']=True
except Exception as error:report['error']=str(error);raise
finally:
 report['trace']=ctx.metadata.get('dual_model_trace',[]);bridge.close();stop_dual();(ROOT/'artifacts/debug/simple-language/baidu-real-result.json').write_text(json.dumps(report,ensure_ascii=False,indent=2),encoding='utf8')
print('REAL_BAIDU_SEARCH_PASS',flush=True)
