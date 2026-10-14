import threading
from http.server import BaseHTTPRequestHandler,ThreadingHTTPServer
import pytest
from agent_runtime import AgentSession
from instructions.common.rpa_bridge import RpaBridge
from instructions.models import ExecutionContext

def test_real_browser_observe_type_click_and_expired_refs(tmp_path,monkeypatch):
    monkeypatch.setenv('ANCLICKER_DATA_DIR',str(tmp_path))
    class Handler(BaseHTTPRequestHandler):
        def do_GET(self):
            body=b'''<html><title>Agent fixture</title><input id="query" placeholder="Search"><input type="password" id="secret" value="DO_NOT_SHARE"><button id="go" onclick="document.querySelector('#result').innerText='Result: '+document.querySelector('#query').value">Search</button><p id="result">Ready</p></html>'''
            self.send_response(200);self.send_header('Content-Type','text/html;charset=utf-8');self.end_headers();self.wfile.write(body)
        def log_message(self,*args):pass
    server=ThreadingHTTPServer(('127.0.0.1',0),Handler);threading.Thread(target=server.serve_forever,daemon=True).start()
    session=AgentSession(RpaBridge('agent-test'));context=ExecutionContext()
    def call(**args):return session.execute('browser',args,context)
    try:
        view=call(action='open',url=f'http://127.0.0.1:{server.server_port}')
        assert view['title']=='Agent fixture'
        assert 'DO_NOT_SHARE' not in str(view)
        assert not any(e.get('type')=='password' for e in view['elements'])
        ref=next(e['ref'] for e in view['elements'] if e['tag']=='input')
        call(action='type',ref=ref,text='AnClicker')
        with pytest.raises(RuntimeError,match='失效'):call(action='type',ref=ref,text='wrong')
        view=call(action='view');ref=next(e['ref'] for e in view['elements'] if e['tag']=='button')
        call(action='click',ref=ref)
        assert 'Result: AnClicker' in call(action='view')['text']
    finally:session.close();server.shutdown();server.server_close()
