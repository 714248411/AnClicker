import threading
import time
import socket
from http.server import BaseHTTPRequestHandler, ThreadingHTTPServer
from test.test_rpa_integration import bridge, call


def test_address_enter_navigates_in_real_browser():
    # The current toolbar lives in its own BrowserView, outside the page DOM.
    import os
    import subprocess
    from pathlib import Path
    root = Path(__file__).resolve().parents[1]
    env = dict(os.environ)
    env.pop('ELECTRON_RUN_AS_NODE', None)
    subprocess.run([str(root/'runtime/electron/electron.exe'),
                    str(root/'test/browser_address_native.cjs')],
                   cwd=root, env=env, check=True, timeout=45)


def test_open_does_not_wait_for_hanging_resource_and_full_wait_times_out(bridge):
    import pytest
    release=threading.Event()
    class Handler(BaseHTTPRequestHandler):
        def do_GET(self):
            if self.path=='/slow.png':
                release.wait(15)
                return
            body=b'<div id="ready">usable</div><img src="/slow.png">'
            self.send_response(200);self.send_header('Content-Type','text/html');self.end_headers();self.wfile.write(body)
        def log_message(self,*args):pass
    server=ThreadingHTTPServer(('127.0.0.1',0),Handler)
    threading.Thread(target=server.serve_forever,daemon=True).start()
    try:
        start=time.monotonic()
        call(bridge,'openUrl',{'url':f'http://127.0.0.1:{server.server_port}','waitType':'加载完成'})
        assert time.monotonic()-start<8
        assert call(bridge,'getText',{'selector':'#ready','by':'CSS选择器','varName':'text'})['variables']['text']=='usable'
        with pytest.raises(RuntimeError,match='超时'):
            call(bridge,'waitPageReady',{'timeout':1})
        release.set()
        call(bridge,'waitPageReady',{'timeout':5})
    finally:release.set();server.shutdown();server.server_close()
