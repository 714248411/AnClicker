"""Isolated real-model check for a built Windows application; invoked explicitly."""
import json,os,time,threading
from pathlib import Path
from http.server import BaseHTTPRequestHandler,ThreadingHTTPServer

def run():
    from agent_runtime import AgentSession
    from agent_provider import AgentSettings
    from agent_protocol import draft_data
    from instructions.models import ExecutionContext
    root=Path(os.environ['ANCLICKER_DATA_DIR']);root.mkdir(parents=True,exist_ok=True)
    class Handler(BaseHTTPRequestHandler):
        def do_GET(self):
            body='''<html><title>Packaged Agent check</title><label>搜索 <input placeholder="搜索" id="q"></label><button onclick="document.querySelector('#result').innerText='成功：'+document.querySelector('#q').value">确认</button><p id="result">等待输入</p></html>'''.encode('utf-8')
            self.send_response(200);self.send_header('Content-Type','text/html;charset=utf-8');self.end_headers();self.wfile.write(body)
        def log_message(self,*args):pass
    server=ThreadingHTTPServer(('127.0.0.1',0),Handler);threading.Thread(target=server.serve_forever,daemon=True).start()
    session=AgentSession();events=[];start=time.monotonic()
    def emit(kind,value):events.append({'kind':kind,'value':value})
    try:
        for text in ['帮我编写一条等待2秒的指令草稿','把第1行的时长改成3秒']:
            session.run(text,AgentSettings(max_steps=6),ExecutionContext(),emit)
        assert len(session.drafts)==1 and session.drafts[0].parameters['时长']==3
        for text in [f'打开 http://127.0.0.1:{server.server_port} 并查看页面','在搜索输入框填写 AnClicker','点击确认按钮']:
            session.run(text,AgentSettings(max_steps=5),ExecutionContext(),emit)
        page=session.execute('browser',{'action':'view'},ExecutionContext())
        assert '成功：AnClicker' in page['text']
        report={'passed':True,'real_model':True,'drafts':[draft_data(d) for d in session.drafts],'browser_result':page['text'],'seconds':round(time.monotonic()-start,2),'events':events}
        result=0
    except Exception as error:
        report={'passed':False,'error':str(error),'events':events};result=1
    finally:session.close();server.shutdown();server.server_close()
    (root/'agent-model-result.json').write_text(json.dumps(report,ensure_ascii=False,indent=2),encoding='utf-8')
    return result
