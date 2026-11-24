import sys, tempfile
from pathlib import Path
from types import SimpleNamespace
sys.path.insert(0,str(Path(__file__).resolve().parents[1]))
from anclicker.platform.cdp_discovery import discover_endpoints
def p(name,*args): return SimpleNamespace(info={'name':name,'cmdline':list(args)})
with tempfile.TemporaryDirectory() as folder:
 Path(folder,'DevToolsActivePort').write_text('12345\n/browser/test')
 pages=discover_endpoints([
 p('chrome.exe','--remote-debugging-port=9222'),
 p('msedge.exe','--remote-debugging-port','9223'),
 p('chrome.exe','--remote-debugging-port=9222'),
 p('chrome.exe','--remote-debugging-port=0','--user-data-dir='+folder),
 p('chrome.exe'),p('other.exe','--remote-debugging-port=9224'),
 p('chrome.exe','--type=renderer','--remote-debugging-port=9225'),
 p('chrome.exe','--remote-debugging-port=-1'),p('chrome.exe','--remote-debugging-port=65536'),
 p('chrome.exe','--remote-debugging-port=bad'),p('chrome.exe','--remote-debugging-port=0')])
 assert [x['endpoint'] for x in pages]==['http://127.0.0.1:9222','http://127.0.0.1:9223','http://127.0.0.1:12345'],pages
print('PASS browser process discovery, dynamic ports, duplicate and invalid endpoint filtering')
