import sys,json,threading,hashlib,time
from pathlib import Path
from http.server import BaseHTTPRequestHandler,ThreadingHTTPServer
from unittest.mock import patch
ROOT=Path(__file__).resolve().parents[1];sys.path.insert(0,str(ROOT))
from models.draft_planner import plan_drafts
from models.agent_provider import AgentSettings
from models.api_planner import parse_json
from anclicker.domain.instructions import ExecutionContext,CommandRecord
from anclicker.domain.agent_protocol import make_draft
from anclicker.instructions.registry import get_instruction_spec
OUT=ROOT/'artifacts/debug/v173-optimize/api';OUT.mkdir(exist_ok=True,parents=True)
queue=[];requests=[];failure=None
class Handler(BaseHTTPRequestHandler):
 def do_POST(self):
  payload=json.loads(self.rfile.read(int(self.headers['Content-Length'])));requests.append({'path':self.path,'native':'tools' in payload,'model':payload['model']})
  assert self.headers['Authorization']=='Bearer protocol-test-only'
  if failure=='http':self.send_response(401);self.end_headers();return
  answer=queue.pop(0);native='tools' in payload
  if native:
   name=payload['tools'][0]['function']['name']
   message={'tool_calls':[{'id':'call_test','type':'function','function':{'name':'wrong_tool' if failure=='tool' else name,'arguments':{'result':answer} if self.path=='/api/chat' else json.dumps({'result':answer},ensure_ascii=False)}}]}
  else:message={'content':json.dumps(answer,ensure_ascii=False)}
  reason='length' if failure=='length' else 'stop'
  response={'message':message,'done_reason':reason} if self.path=='/api/chat' else {'choices':[{'message':message,'finish_reason':reason}]}
  body=json.dumps(response,ensure_ascii=False).encode();self.send_response(200);self.send_header('Content-Type','application/json');self.send_header('Content-Length',str(len(body)));self.end_headers();self.wfile.write(body)
 def log_message(self,*args):pass
server=ThreadingHTTPServer(('127.0.0.1',0),Handler);threading.Thread(target=server.serve_forever,daemon=True).start()
endpoint=f'http://127.0.0.1:{server.server_port}';rows=[]
def step(t,**p):return {'type_id':t,'parameters':p}
def settings(backend,mode):return AgentSettings(backend=backend,mode=mode,endpoint=endpoint+('/v1' if backend=='compatible' else ''),model='api-test-model',api_key='protocol-test-only')
def record(name,passed=True,**extra):rows.append({'name':name,'passed':passed,**extra});print('PASS',name,flush=True)
try:
 with patch('models.dual_model.manager',side_effect=AssertionError('API 不应启动本地模型')):
  for backend in ['compatible','ollama']:
   for mode in ['json','native']:
    config=settings(backend,mode);ctx=ExecutionContext()
    expected=[step('打开网页',url='https://www.baidu.com'),step('输入文本',selector='textarea#chat-textarea, input[name="wd"]',by='CSS选择器',text='热点',pressEnter='是',clear='是')]
    queue[:]=[{'boundaries':[True]},*expected]
    response=plan_drafts('打开百度，搜索热点',config,ctx)
    items=response['arguments']['instructions'];assert [{k:v for k,v in i.items() if k!='note'} for i in items]==expected
    assert len(ctx.metadata['dual_model_trace'])==3 and not queue
    record(backend+' '+mode+' 百度两步',trace_roles=[t['role'] for t in ctx.metadata['dual_model_trace']])
    before=len(requests);r=plan_drafts('把表格内容填入到网页里对应后面，按顺序填入',config,ExecutionContext())
    assert r['arguments']['instructions'][0]['type_id']=='表格填入网页' and len(requests)==before
    record(backend+' '+mode+' 表格直接绑定')
    folder=OUT/(backend+'-'+mode+'-'+str(time.time_ns()));folder.mkdir();source=folder/'原文.txt';dest=folder/'副本.txt';source.write_text('测试😀\n第二行\n',encoding='utf8');digest=hashlib.sha256(source.read_bytes()).hexdigest()
    request=f'复制“{source.as_posix()}”到“{dest.as_posix()}”，保留原文件，然后计算文件“{dest.as_posix()}”的SHA256'
    queue[:]=[{'boundaries':[False,True]},step('快速文件操作',操作='复制',源路径=source.as_posix(),目标路径=dest.as_posix()),step('运行Python',代码='import hashlib\nfrom pathlib import Path\nresult = hashlib.sha256(Path(inputs[0]).read_bytes()).hexdigest()',返回值='result',变量='Python返回值')]
    ctx=ExecutionContext();r=plan_drafts(request,config,ctx);values=[]
    for item in r['arguments']['instructions']:
     d=make_draft(**item);values.append(get_instruction_spec(d.type_id).create_executor().execute(ctx,CommandRecord(None,d.type_id,d.parameters)))
    assert values[-1]==digest and source.read_bytes()==dest.read_bytes() and not queue
    record(backend+' '+mode+' 文件复制及内部Python实际执行',executed=2)
  from anclicker.execution.agent_runtime import AgentSession
  session=AgentSession();events=[];config=settings('compatible','native');config.verify_before_draft=False
  queue[:]=[{'boundaries':[True]},*expected]
  try:
   session.run('打开百度，搜索热点',config,ExecutionContext(),lambda k,v:events.append((k,v)))
   assert len(session.drafts)==2 and any(k=='drafts' for k,v in events)
   record('API界面会话入口生成两步草稿')
  finally:session.close()
  config=settings('compatible','json')
  for name,answer,kind in [('编造网址',[{'boundaries':[]},step('打开网页',url='https://invented.invalid')],None),('截断',[{'boundaries':[]}],'length'),('认证失败',[{'boundaries':[]}],'http')]:
   queue[:]=answer;failure=kind
   try:plan_drafts('打开百度',config,ExecutionContext())
   except (ValueError,RuntimeError) as e:assert 'protocol-test-only' not in str(e);record('拒绝'+name,error=str(e))
   else:raise AssertionError('没有拒绝'+name)
   failure=None
  failure='tool';queue[:]=[{'boundaries':[]}]
  try:plan_drafts('打开百度',settings('compatible','native'),ExecutionContext())
  except ValueError:record('拒绝错误工具名')
  else:raise AssertionError('错误工具名被接受')
  failure=None
  assert parse_json(chr(96)*3+'json\n{"boundaries":[]}\n'+chr(96)*3)=={'boundaries':[]};record('兼容单个JSON代码块')
finally:
 server.shutdown();(OUT/'results.json').write_text(json.dumps({'passed':sum(x['passed'] for x in rows),'total':18,'cases':rows,'requests':requests,'scope':'Local HTTP protocol fixture, not a live cloud model accuracy evaluation'},ensure_ascii=False,indent=2),encoding='utf8')
assert len(rows)==18
print('API_PARITY_PASS',len(rows),flush=True)
