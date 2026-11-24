"""Authenticated localhost API for external models; drafts remain unexecuted."""
import argparse
import hmac
import json
import os
import secrets
import threading
from http.server import BaseHTTPRequestHandler, ThreadingHTTPServer
from pathlib import Path
from urllib.parse import urlsplit
from anclicker.domain.agent_protocol import TOOLS, VERSION, catalog, instruction_schema, envelope, export_drafts, SYSTEM_PROMPT
from anclicker.domain.agent_execution_policy import POLICY_VERSION, INTEGRATION_GUIDE
from anclicker.domain.instructions import ExecutionContext
from anclicker.execution.agent_runtime import AgentSession

DRAFT_TOOLS={'cmd_reference','instructions_search','instruction_schema','draft_read','draft_append','draft_append_batch','draft_update','workflow_read','workflow_patch'}

class ToolAPIServer(ThreadingHTTPServer):
    daemon_threads=True
    def __init__(self,address,token,allow_browser=False,allow_system=False):
        self.token=token;self.allow_browser=allow_browser;self.allow_system=allow_system
        self.sessions={};self.lock=threading.RLock()
        super().__init__(address,Handler)
    def allowed(self,name):
        return name in DRAFT_TOOLS or (self.allow_browser and name in {'browser','crawl_page'}) or (self.allow_system and name in {'system_file','verify_screen'})
    def server_close(self):
        with self.lock:
            for session in self.sessions.values():session.close()
        super().server_close()

class Handler(BaseHTTPRequestHandler):
    def log_message(self,*args):pass
    def send_json(self,status,value):
        body=json.dumps(value,ensure_ascii=False).encode('utf-8')
        self.send_response(status);self.send_header('Content-Type','application/json; charset=utf-8')
        self.send_header('Content-Length',str(len(body)));self.end_headers();self.wfile.write(body)
    def authorized(self):
        given=self.headers.get('Authorization','')
        return hmac.compare_digest(given,'Bearer '+self.server.token)
    def do_GET(self):
        if not self.authorized():self.send_json(401,{'error':'Unauthorized'});return
        path=urlsplit(self.path).path
        if path=='/v1/tools':
            self.send_json(200,{'protocol':VERSION,'tools':[t for t in TOOLS if self.server.allowed(t['function']['name'])]})
        elif path=='/v1/guide':
            self.send_json(200,{'protocol':VERSION,'guide_version':POLICY_VERSION,
                'system_prompt':SYSTEM_PROMPT,'integration_guide':INTEGRATION_GUIDE,
                'workflow_scope':'session_drafts',
                'tools':[t for t in TOOLS if self.server.allowed(t['function']['name'])]})
        elif path=='/v1/instructions':
            self.send_json(200,{'instructions':[instruction_schema(item['type_id']) for item in catalog()]})
        else:self.send_json(404,{'error':'Not found'})
    def do_POST(self):
        if not self.authorized():self.send_json(401,{'error':'Unauthorized'});return
        try:
            length=int(self.headers.get('Content-Length','0'))
            if not 0<length<=256000:raise ValueError('请求大小必须为 1 到 256000 字节')
            body=json.loads(self.rfile.read(length))
            if not isinstance(body,dict):raise ValueError('请求必须为 JSON 对象')
            path=urlsplit(self.path).path
            with self.server.lock:
                if path=='/v1/sessions':
                    if len(self.server.sessions)>=16:raise ValueError('会话数已满，请关闭旧会话')
                    session_id=secrets.token_urlsafe(24)
                    self.server.sessions[session_id]=AgentSession()
                    self.send_json(201,{'session_id':session_id});return
                session_id=body.get('session_id','')
                if session_id not in self.server.sessions:raise ValueError('未知会话')
                session=self.server.sessions[session_id]
                if path=='/v1/tools/call':
                    name=body.get('name','')
                    if not self.server.allowed(name):raise ValueError('此工具未启用；系统工具需 --allow-system')
                    try:result=envelope(name,session.execute(name,body.get('arguments',{}),ExecutionContext()))
                    except Exception as error:result=envelope(name,error=error)
                    self.send_json(200,result)
                elif path=='/v1/drafts/export':self.send_json(200,export_drafts(session.drafts))
                elif path=='/v1/sessions/close':
                    session.close();del self.server.sessions[session_id];self.send_json(200,{'closed':True})
                else:self.send_json(404,{'error':'Not found'})
        except (ValueError,TypeError,KeyError) as error:self.send_json(400,{'error':str(error)})

def main():
    parser=argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--port',type=int,default=8767)
    parser.add_argument('--allow-browser',action='store_true',help='Also allow live browser and Crawl4AI tools')
    parser.add_argument('--allow-system',action='store_true',help='Allow local file actions and screenshot OCR verification')
    args=parser.parse_args()
    token=os.environ.get('ANCLICKER_TOOL_API_TOKEN') or secrets.token_urlsafe(32)
    server=ToolAPIServer(('127.0.0.1',args.port),token,args.allow_browser,args.allow_system)
    print('URL: http://127.0.0.1:'+str(server.server_port),flush=True)
    print('Bearer token: '+token,flush=True)
    try:server.serve_forever()
    except KeyboardInterrupt:pass
    finally:server.server_close()

if __name__=='__main__':main()
