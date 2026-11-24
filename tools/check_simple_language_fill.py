import sys,json,threading,hashlib
from pathlib import Path
from http.server import BaseHTTPRequestHandler,ThreadingHTTPServer
from unittest.mock import patch
ROOT=Path(__file__).resolve().parents[1];sys.path.insert(0,str(ROOT))
from models.draft_planner import plan_drafts
from models.agent_provider import AgentSettings
from models.dual_model import stop_dual
from anclicker.domain.instructions import ExecutionContext,CommandRecord
from anclicker.domain.agent_protocol import make_draft
from anclicker.instructions.registry import get_instruction_spec
from anclicker.platform.rpa_bridge import RpaBridge
OUT=ROOT/'artifacts/debug/simple-language';SOURCE=OUT/'source.xlsx'
def page(kind):
 names=['编号','姓名','备注']*2 if kind=='match' else ['姓名','编号','备注']*2
 if kind=='missing':names[-1]='不对应'
 if kind=='count':names=names[:-1]
 fields=''.join(f'<label>{name}'+('<select><option>原值</option><option>${secret}</option><option>O&#39;Brien😀</option></select>' if kind=='select' and name=='备注' else '<input value="原值">')+'</label>' for name in names)
 return '<!doctype html><meta charset="utf-8">'+fields+'''<input type="hidden" value="隐藏"><input type="password" value="密码"><pre id="state"></pre><script>function sync(){document.querySelector('#state').textContent=JSON.stringify(Array.from(document.querySelectorAll('label input,label select')).map(x=>x.value));}document.addEventListener('input',sync);sync();</script>'''
class Handler(BaseHTTPRequestHandler):
 def do_GET(self):
  body=page(self.path.strip('/')).encode();self.send_response(200);self.send_header('Content-Type','text/html;charset=utf-8');self.end_headers();self.wfile.write(body)
 def log_message(self,*args):pass
server=ThreadingHTTPServer(('127.0.0.1',0),Handler);threading.Thread(target=server.serve_forever,daemon=True).start();url=f'http://127.0.0.1:{server.server_port}'
bridge=RpaBridge('simple-language-acceptance');rows=[];before=hashlib.sha256(SOURCE.read_bytes()).hexdigest()
def execute(text):
 ctx=ExecutionContext();ctx.variables['secret']='不能被代入'
 response=plan_drafts(text,AgentSettings(local_profile='cpu'),ctx)
 assert response['type']=='tool_call',response
 with patch('anclicker.instructions.common.rpa_instruction.get_bridge',return_value=bridge):
  for item in response['arguments']['instructions']:
   draft=make_draft(**item);get_instruction_spec(draft.type_id).create_executor().execute(ctx,CommandRecord(None,draft.type_id,draft.parameters))
 return response
try:
 bridge.execute({'id':'excelOpen','params':{'path':SOURCE.as_posix(),'sheetName':'数据'}})
 tests=[('select','把表格按表头对应填入网页',False),('match','把表格内容填入到网页里对应后面，按顺序填入',False),('order','把当前表格按顺序填入当前网页',False),('order','把表格A2:C3的内容按顺序填入网页，无表头',False),('missing','把表格按表头对应填入网页',True),('count','把表格按顺序填入网页',True)]
 for kind,text,reject in tests:
  bridge.execute({'id':'openUrl','params':{'url':url+'/'+kind}});row={'request':text,'passed':False}
  try:
   row['plan']=execute(text)
   assert not reject,'应当拒绝不匹配'
  except Exception as error:
   row['error']=str(error)
   if not reject:raise
   assert any(word in str(error) for word in ['输入框','数量','字段']),str(error)
  actual=bridge.execute({'id':'getText','params':{'selector':'#state','by':'CSS选择器','varName':'state'}})['variables']['state'];actual=json.loads(actual)
  expected=['原值']*(5 if kind=='count' else 6) if reject else ['00123','张三','${secret}','00007','李四',"O'Brien😀"] if kind=='match' else ['张三','00123','${secret}','李四','00007',"O'Brien😀"]
  assert actual==expected,(actual,expected)
  row.update(passed=True,actual=actual,rejected_before_write=reject);rows.append(row);print('PASS',text,flush=True)
 assert hashlib.sha256(SOURCE.read_bytes()).hexdigest()==before
finally:
 bridge.close();server.shutdown();stop_dual();(OUT/'fill-results.json').write_text(json.dumps({'passed':sum(x['passed'] for x in rows),'total':6,'cases':rows},ensure_ascii=False,indent=2),encoding='utf8')
