"""Release-only fixture checks for instruction resources and imports."""
import threading
from http.server import BaseHTTPRequestHandler, ThreadingHTTPServer
from tempfile import TemporaryDirectory
from pathlib import Path
from anclicker.instructions.registry import INSTRUCTION_SPECS
from anclicker.domain.instructions import ExecutionContext
from anclicker.storage.database import DatabaseOperation

def validate_dependencies():
    with TemporaryDirectory(prefix='instruction-check-') as folder:
        database = DatabaseOperation(str(Path(folder) / 'checks.db'))
        for spec in INSTRUCTION_SPECS:
            spec.create_executor()
            spec.parameter_fields()
            editor = spec.create_editor(context=ExecutionContext(metadata={'database': database}))
            editor.close()
            editor.deleteLater()
    class Handler(BaseHTTPRequestHandler):
        def do_GET(self):
            body = b'<html><title>offline fixture</title><main><p>Portable extraction test 12345</p><video src="/sample.mp4"></video></main></html>'
            self.send_response(200)
            self.send_header('Content-Type', 'text/html; charset=utf-8')
            self.end_headers()
            self.wfile.write(body)
        def log_message(self, *args): pass
    server = ThreadingHTTPServer(('127.0.0.1', 0), Handler)
    threading.Thread(target=server.serve_forever, daemon=True).start()
    try:
        from anclicker.platform.crawl4ai_bridge import crawl_page
        from anclicker.platform.extraction_export import export_extracted
        result = crawl_page('http://127.0.0.1:' + str(server.server_port), selector='main')
        assert '12345' in result['text'] and result['videos'][0]['url'].endswith('/sample.mp4'), result
        with TemporaryDirectory() as folder:
            for kind in ('Word', 'Excel', 'TXT'):
                export_extracted(result, Path(folder) / kind, kind)
    finally:
        server.shutdown()
    return {'editors': len(INSTRUCTION_SPECS), 'executors': len(INSTRUCTION_SPECS), 'crawl4ai': True, 'exports': True}
