import json
import tempfile
import threading
import time
import sys
from pathlib import Path
if __package__ in (None, ""):
 sys.path.insert(0, str(Path(__file__).resolve().parents[1]))
from http.server import BaseHTTPRequestHandler, ThreadingHTTPServer
from anclicker.platform.crawl4ai_bridge import crawl_page
from anclicker.domain.instructions import ExecutionContext, CommandRecord
from anclicker.instructions.registry import get_instruction_spec
from anclicker.execution.agent_runtime import AgentSession
from anclicker.domain.agent_protocol import instruction_schema
class Handler(BaseHTTPRequestHandler):
 def do_GET(self):
  if self.path=='/missing':self.send_error(404);return
  self.send_response(200);self.send_header('Content-Type','text/html; charset=utf-8');self.end_headers()
  self.wfile.write('<html><head><title>Crawl4AI验收</title></head><body><nav>不要提取的导航</nav><main id="article"><h1>网页抓取验收</h1><p>这是 AnClicker 的正文提取测试。 This page verifies article extraction, readable Markdown, links, saved variables and browser cleanup. 这是 AnClicker 的正文提取测试。 This page verifies article extraction, readable Markdown, links, saved variables and browser cleanup. 这是 AnClicker 的正文提取测试。 This page verifies article extraction, readable Markdown, links, saved variables and browser cleanup. 这是 AnClicker 的正文提取测试。 This page verifies article extraction, readable Markdown, links, saved variables and browser cleanup. 这是 AnClicker 的正文提取测试。 This page verifies article extraction, readable Markdown, links, saved variables and browser cleanup. 这是 AnClicker 的正文提取测试。 This page verifies article extraction, readable Markdown, links, saved variables and browser cleanup. 这是 AnClicker 的正文提取测试。 This page verifies article extraction, readable Markdown, links, saved variables and browser cleanup. 这是 AnClicker 的正文提取测试。 This page verifies article extraction, readable Markdown, links, saved variables and browser cleanup. 这是 AnClicker 的正文提取测试。 This page verifies article extraction, readable Markdown, links, saved variables and browser cleanup. 这是 AnClicker 的正文提取测试。 This page verifies article extraction, readable Markdown, links, saved variables and browser cleanup. 这是 AnClicker 的正文提取测试。 This page verifies article extraction, readable Markdown, links, saved variables and browser cleanup. 这是 AnClicker 的正文提取测试。 This page verifies article extraction, readable Markdown, links, saved variables and browser cleanup. </p><a href="/next">下一页</a><img src="/picture.png" alt="测试图片"><video preload="none" src="/sample.mp4"></video><table><tr><th>名称</th><th>数量</th></tr><tr><td>测试</td><td>2</td></tr></table></main><script>setTimeout(()=>{let p=document.createElement("p");p.id="ready";p.textContent="动态内容已加载";document.querySelector("main").appendChild(p)},200)</script></body></html>'.encode())
 def log_message(self,*args):pass
server=ThreadingHTTPServer(('127.0.0.1',0),Handler)
threading.Thread(target=server.serve_forever,daemon=True).start()
url='http://127.0.0.1:'+str(server.server_port)
try:
 result=crawl_page(url,selector='#article',wait_for='#ready')
 assert '动态内容已加载' in result['markdown'],result
 assert '不要提取的导航' not in result['text'],result
 assert result['links'] and result['title']=='Crawl4AI验收',result
 assert result['images'][0]['url']==url+'/picture.png',result
 assert result['videos'][0]['url']==url+'/sample.mp4',result
 assert result['tables'][0]['headers']==['名称','数量'],result
 assert result['tables'][0]['rows']==[['测试','2']],result
 print('PASS bundled Electron dynamic content, selector, title, links, images and tables',flush=True)
 spec=get_instruction_spec('Crawl4AI网页抓取');assert spec.category=='网页抓取工具'
 context=ExecutionContext(variables={'目标网址':url})
 cmd=CommandRecord(None,spec.type_id,{'网址':'{{目标网址}}','格式':'正文','变量':'结果'})
 value=spec.create_executor().execute_once(context,cmd)
 assert context.variables['结果']==value and '网页抓取验收' in value
 assert instruction_schema(spec.type_id)['defaults']['超时']==60
 assert context.metadata['last_web_extraction']==value
 with tempfile.TemporaryDirectory() as directory:
  for kind in ('Word','Excel','TXT'):
   export_spec=get_instruction_spec('提取转'+kind)
   export_command=CommandRecord(None,export_spec.type_id,{'保存路径':str(Path(directory)/kind)})
   saved=export_spec.create_executor().execute_once(context,export_command)
   assert Path(saved).is_file()
 print('PASS instruction execution and automatic export to Word, Excel and TXT',flush=True)
 session=AgentSession()
 value=session.execute('crawl_page',{'url':url},ExecutionContext());assert '网页抓取验收' in value['markdown']
 session.close();print('PASS Agent tool execution',flush=True)
 try:crawl_page(url+'/missing')
 except RuntimeError:pass
 else:raise AssertionError('404 should fail')
 context=ExecutionContext();threading.Timer(2,lambda:setattr(context,'stop_requested',True)).start()
 started=time.monotonic()
 try:crawl_page(url,context,wait_for='#never',timeout=30)
 except InterruptedError:pass
 else:raise AssertionError('cancel should interrupt')
 assert time.monotonic()-started<12
 print('PASS HTTP failure and cancellation cleanup',flush=True)
finally:server.shutdown()
