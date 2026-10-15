"""Validate the bundled engine using temporary workbooks and a local web page."""
from pathlib import Path
from tempfile import TemporaryDirectory
from http.server import BaseHTTPRequestHandler, ThreadingHTTPServer
import threading
from openpyxl import load_workbook
from anclicker.platform.rpa_bridge import RpaBridge

from anclicker._imports import DeferredImports as _DeferredImports

# Dependencies declared here retain their existing on-demand loading boundaries.
_module_imports = _DeferredImports(globals(), {
    'events_to_web_drafts': ('from', 'anclicker.execution.web_recording', ('events_to_web_drafts',), 0),
})


def validate_rpa():
    class Handler(BaseHTTPRequestHandler):
        def do_GET(self):
            body=b'''<title>test</title><input id="name"><button id="go" onclick="document.querySelector('#result').textContent=document.querySelector('#name').value">Run</button><div id="result">ready</div>'''
            self.send_response(200);self.send_header('Content-Type','text/html; charset=utf-8');self.end_headers();self.wfile.write(body)
        def log_message(self,*args): pass
    bridge=RpaBridge()
    def run(kind, params=None): return bridge.execute({'id':kind,'params':params or {}})
    server=ThreadingHTTPServer(('127.0.0.1',0),Handler)
    threading.Thread(target=server.serve_forever,daemon=True).start()
    try:
        with TemporaryDirectory(prefix='rpa-smoke-') as temp:
            folder=Path(temp);book=folder/'test.xlsx'
            run('excelNew',{'path':str(book),'sheetName':'Sheet1'})
            run('excelWrite',{'cell':'A1','value':'packaged Excel'})
            run('excelSave',{'path':''})
            wb=load_workbook(book)
            assert wb.active['A1'].value=='packaged Excel'
            wb.close()
            run('openUrl',{'url':f'http://127.0.0.1:{server.server_port}','target':'新窗口','loginMode':'独立登录(每次全新)','engine':'跟随当前','waitType':'加载完成'})
            run('input',{'selector':'#name','by':'CSS选择器','text':'packaged browser','clear':'是','pressEnter':'否'})
            run('click',{'selector':'#go','by':'CSS选择器','clickType':'单击'})
            assert run('getText',{'selector':'#result','by':'CSS选择器','varName':'output'})['variables']['output']=='packaged browser'
            assert run('acInspect')['result']['titles']==['极速网页AC']
            image=folder/'screenshot.png'
            run('screenshot',{'selector':'#result','path':str(image)})
            assert image.read_bytes().startswith(bytes([137,80,78,71]))
            run('input',{'selector':'#name','by':'CSS选择器','text':'','clear':'是','pressEnter':'否'})
            run('acRecordStart')
            run('pressKey',{'key':'自定义','customKey':'a'})
            recording=run('acRecordStop')['result']
            assert any(e['type']=='input' and e['selector']=='#name' for e in recording['events'])
            events_to_web_drafts = _module_imports.load('events_to_web_drafts')
            assert any(d.type_id=='等待（秒）' for d in events_to_web_drafts('http://127.0.0.1',recording['events'],recording['elapsed']))
        return {'excel':True,'browser':True,'screenshot':True,'title':'极速网页AC','web_recording':True}
    finally:
        bridge.close();server.shutdown();server.server_close()

if __name__ == '__main__':
    print(validate_rpa())
