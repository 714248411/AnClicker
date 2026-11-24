import os, sys, tempfile, threading
from pathlib import Path
from http.server import BaseHTTPRequestHandler, ThreadingHTTPServer
ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT))
sys.path.insert(0, str(ROOT / 'integrations/crawl4ai'))
os.environ['QT_QPA_PLATFORM'] = 'offscreen'
sys.path.append(str(ROOT / '.local/runtimes/crawl4ai/venv/Lib/site-packages'))
from extraction import extract_common
from anclicker.platform.video_download import download_video
payload = b'\x00\x00\x00\x18ftypmp42' + b'x' * 150000
class Handler(BaseHTTPRequestHandler):
    def do_GET(self):
        body = b'<html>login</html>' if self.path == '/bad' else payload
        self.send_response(200)
        self.send_header('Content-Type', 'application/octet-stream')
        self.send_header('Content-Length', str(len(body)))
        self.end_headers()
        self.wfile.write(body)
    def log_message(self, *args): pass
server = ThreadingHTTPServer(('127.0.0.1', 0), Handler)
threading.Thread(target=server.serve_forever, daemon=True).start()
base = 'http://127.0.0.1:' + str(server.server_port)
try:
    result = extract_common('<video src="/a.mp4"><source src="/a.mp4"></video><video src="blob:abc"></video><a href="/v.m3u8">stream</a><audio><source src="/a.mp3"></audio>', base)
    assert len(result['videos']) == 3, result
    assert extract_common('<div id="x"></div><video src="/a.mp4"></video>', base, '#x')['videos'] == []
    with tempfile.TemporaryDirectory() as d:
        path = Path(d) / 'test.mp4'
        download_video(base + '/a.mp4', path)
        assert path.read_bytes() == payload
        for url, cancel in [(base + '/bad', lambda: False), (base + '/a.mp4', lambda: True), (base + '/a.m3u8', lambda: False)]:
            try: download_video(url, path, cancelled=cancel)
            except (ValueError, InterruptedError): pass
            else: raise AssertionError('Expected failure')
            assert path.read_bytes() == payload
        assert list(Path(d).iterdir()) == [path]
    from anclicker.platform.qt_compat.QtWidgets import QApplication
    app = QApplication.instance() or QApplication([])
    from anclicker.ui.instruction_editors.网页抓取工具.网页视频提取 import InstructionEditor
    from anclicker.instructions.registry import get_instruction_spec
    spec = get_instruction_spec('网页视频提取')
    assert spec.create_executor().OUTPUT_FORMAT == '视频'
    editor = spec.create_editor()
    assert editor.ui.parameterGroupBox.title() == '网页视频提取参数'
    assert editor._controls['格式'].currentText() == '视频'
    from anclicker.ui.instruction_editors.extensions.crawl_preview import CrawlResultDialog
    dialog = CrawlResultDialog({'videos': result['videos']}, selected='视频')
    assert dialog.tabs.tabText(dialog.tabs.currentIndex()) == '视频'
    assert dialog.video_save.isEnabled()
    dialog.close(); editor.close()
    print('PASS: video extraction, selector, download bytes, cancellation, invalid content, atomic cleanup, editor and preview')
finally:
    server.shutdown()
