import sys,json,threading,hashlib,subprocess
from pathlib import Path
from http.server import BaseHTTPRequestHandler,ThreadingHTTPServer
from unittest.mock import patch
ROOT=Path(__file__).resolve().parents[1];sys.path.insert(0,str(ROOT));OUT=ROOT/'artifacts/debug/spreadsheet-web'
from models.draft_planner import plan_drafts
from models.agent_provider import AgentSettings
from anclicker.domain.instructions import ExecutionContext,CommandRecord
from anclicker.domain.agent_protocol import make_draft
from anclicker.instructions.registry import get_instruction_spec
from anclicker.platform.rpa_bridge import RpaBridge
HTML='''<!doctype html><meta charset="utf-8"><title>表格往返验收</title><textarea id="input" oninput="document.querySelector('#result').textContent=this.value" onchange="document.querySelector('#result').textContent=this.value"></textarea><pre id="result"></pre><div class="values">00123</div><div class="values">=2+2</div><div class="values">中文</div>'''
class Handler(BaseHTTPRequestHandler):
 def do_GET(self):
  body=HTML.encode();self.send_response(200);self.send_header('Content-Type','text/html;charset=utf-8');self.send_header('Content-Length',str(len(body)));self.end_headers();self.wfile.write(body)
 def log_message(self,*args):pass
server=ThreadingHTTPServer(('127.0.0.1',0),Handler);threading.Thread(target=server.serve_forever,daemon=True).start()
url='http://127.0.0.1:'+str(server.server_port)
source=(OUT/'source.xlsx').as_posix();target=(OUT/'result.xlsx').as_posix();before=hashlib.sha256(Path(source).read_bytes()).hexdigest()
text=f'把表格“{source}”工作表“数据”的A1:B2复制到网页 {url} 的 CSS #input，然后提取网页 CSS #result 的文字写入表格“{target}”工作表“结果”的C3'
ctx=ExecutionContext();ctx.variables['secret']='不得泄露';bridge=RpaBridge('spreadsheet-web-acceptance')
report={'request':text,'passed':False,'steps':[]}
try:
 response=plan_drafts(text,AgentSettings(),ctx);report['plan']=response
 with patch('anclicker.instructions.common.rpa_instruction.get_bridge',return_value=bridge):
  for item in response['arguments']['instructions']:
   d=make_draft(**item);r=get_instruction_spec(d.type_id).create_executor().execute(ctx,CommandRecord(None,d.type_id,d.parameters));report['steps'].append({'type':d.type_id,'result':r});print('EXECUTED',d.type_id,flush=True)
  extra=f'提取当前网页 CSS .values 的全部文字写入表格“{target}”工作表“结果”的E1'
  r=plan_drafts(extra,AgentSettings(),ctx)
  for item in r['arguments']['instructions']:
   d=make_draft(**item);get_instruction_spec(d.type_id).create_executor().execute(ctx,CommandRecord(None,d.type_id,d.parameters))
 try:bridge.execute({'id':'excelOpen','params':{'path':source,'sheetName':'不存在的工作表'}})
 except RuntimeError as error:assert '工作表' in str(error);report['missing_sheet_rejected']=True
 else:raise AssertionError('Missing sheet silently accepted')
 assert hashlib.sha256(Path(source).read_bytes()).hexdigest()==before
 check=subprocess.run(['node','tools/spreadsheet_web_fixture.cjs','verify'],cwd=ROOT,capture_output=True,text=True,encoding='utf8');assert check.returncode==0,check.stderr
 report.update(passed=True,verified=json.loads(check.stdout),source_unchanged=True)
except Exception as error:report['error']=str(error);raise
finally:
 bridge.close();server.shutdown();(OUT/'roundtrip-result.json').write_text(json.dumps(report,ensure_ascii=False,indent=2,default=str),encoding='utf8')
print('REAL_ROUNDTRIP_PASS',flush=True)
