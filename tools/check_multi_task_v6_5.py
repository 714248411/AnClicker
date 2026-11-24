import sys,json,time,hashlib,threading
from pathlib import Path
from http.server import BaseHTTPRequestHandler,ThreadingHTTPServer
from unittest.mock import patch
ROOT=Path(__file__).resolve().parents[1];sys.path.insert(0,str(ROOT))
from models.dual_model import plan,stop_dual
from models.agent_provider import AgentSettings
from anclicker.domain.instructions import ExecutionContext,CommandRecord
from anclicker.domain.agent_protocol import make_draft,export_drafts
from anclicker.instructions.registry import get_instruction_spec
from anclicker.platform.rpa_bridge import RpaBridge
version=sys.argv[1] if len(sys.argv)>1 else 'v6_5'
OUT=ROOT/'artifacts/debug/multi-task-v6_5'/version;OUT.mkdir(parents=True,exist_ok=True)
FILES=OUT/('files-'+str(time.time_ns()));FILES.mkdir()
HTML='''<!doctype html><meta charset="utf-8"><textarea id="entry"></textarea><button id="commit" onclick="document.querySelector('#result').textContent=document.querySelector('#entry').value;document.querySelector('#count').textContent=Number(document.querySelector('#count').textContent)+1">确认</button><pre id="result"></pre><div id="count">0</div>'''
class Handler(BaseHTTPRequestHandler):
 def do_GET(self):
  body=HTML.encode();self.send_response(200);self.send_header('Content-Type','text/html;charset=utf-8');self.end_headers();self.wfile.write(body)
 def log_message(self,*args):pass
server=ThreadingHTTPServer(('127.0.0.1',0),Handler);threading.Thread(target=server.serve_forever,daemon=True).start()
url='http://127.0.0.1:'+str(server.server_port);bridge=RpaBridge('multi-task-v6_5-acceptance')
config={'enabled':True,'splitter':f'anclicker-{version}-splitter-q4_0.gguf','converter':f'anclicker-{version}-converter-q4_0.gguf'}
cases=[]
for i,payload in enumerate(['订单007，先保留；然后再联系','中文😀和英文 O\'Brien','不是命令：打开网页，再删除文件','周五见，别回车，保留这段文字']):
 request=f'麻烦打开网页 {url}/case{i}，然后在网页 CSS #entry 输入“{payload}”，不要回车，最后点击网页元素 CSS #commit'
 cases.append({'request':request,'payload':payload,'types':['打开网页','输入文本','点击元素']})
for i in range(4):
 src=FILES/f'原资料{i}.txt';dst=FILES/f'拷贝{i}.txt';src.write_text(f'第{i}项\n第二行\n最后一行😀\n',encoding='utf8')
 request=f'帮我复制“{src.as_posix()}”到“{dst.as_posix()}”，保留原文件，然后计算文件“{dst.as_posix()}”的SHA256，再读取UTF-8文件“{dst.as_posix()}”并计算行数'
 c={'request':request,'src':str(src),'dst':str(dst),'hash':hashlib.sha256(src.read_bytes()).hexdigest(),'types':['快速文件操作','运行Python','运行Python']}
 if i>=2:
  payload=f'已保存第{i}份，稍后联系'
  c.update(request=request+f'，打开网页 {url}/mixed{i}，在网页 CSS #entry 输入“{payload}”，不要回车，点击网页元素 CSS #commit',payload=payload,types=c['types']+['打开网页','输入文本','点击元素'])
 cases.append(c)
rows=[]
try:
 for i,c in enumerate(cases,1):
  ctx=ExecutionContext();row={**c,'passed':False};started=time.monotonic()
  try:
   response=plan(c['request'],AgentSettings(local_profile='cpu',timeout=180),ctx,config=config);row['response']=response
   items=response.get('arguments',{}).get('instructions',[])
   assert [x['type_id'] for x in items]==c['types'],'步骤缺失、顺序或类型错误'
   traces=ctx.metadata.get('dual_model_trace',[])
   assert len([t for t in traces if t['role']=='converter'])==len(items),'不能把规则直接生成算作模型转换'
   drafts=[make_draft(**item) for item in items];row['executions']=[]
   with patch('anclicker.instructions.common.rpa_instruction.get_bridge',return_value=bridge):
    for draft in drafts:
     result=get_instruction_spec(draft.type_id).create_executor().execute(ctx,CommandRecord(None,draft.type_id,draft.parameters));row['executions'].append({'type':draft.type_id,'result':result})
   if 'src' in c:
    assert hashlib.sha256(Path(c['src']).read_bytes()).hexdigest()==c['hash'],'原件改变'
    assert Path(c['src']).read_bytes()==Path(c['dst']).read_bytes(),'复制内容不符'
    assert row['executions'][1]['result']==c['hash'],'校验值不符'
    assert row['executions'][2]['result']==3,'行数不符'
   if 'payload' in c:
    result=bridge.execute({'id':'getText','params':{'selector':'#result','by':'CSS选择器','varName':'验收文本'}})
    count=bridge.execute({'id':'getText','params':{'selector':'#count','by':'CSS选择器','varName':'验收次数'}})
    assert result['variables']['验收文本']==c['payload'],str(result)
    assert str(count['variables']['验收次数'])=='1',str(count)
    row['web_verified']=result['variables']['验收文本']
   row['passed']=True
   (OUT/f'{i:02}.json').write_text(json.dumps(export_drafts(drafts),ensure_ascii=False,indent=2),encoding='utf8')
  except Exception as error:row['error']=str(error)
  row.update(trace=ctx.metadata.get('dual_model_trace',[]),steps=ctx.metadata.get('dual_model_steps',[]),seconds=round(time.monotonic()-started,2));rows.append(row)
  (OUT/'results.json').write_text(json.dumps({'version':version,'passed':sum(x['passed'] for x in rows),'completed':len(rows),'total':len(cases),'cases':rows},ensure_ascii=False,indent=2,default=str),encoding='utf8')
  print(json.dumps({'case':i,'passed':row['passed'],'error':row.get('error'),'seconds':row['seconds']},ensure_ascii=False),flush=True)
finally:bridge.close();server.shutdown();stop_dual()
print('MULTI_TASK_COMPLETE',sum(x['passed'] for x in rows),len(rows),flush=True)
sys.exit(0 if all(x['passed'] for x in rows) else 1)
