"""Find loopback CDP endpoints advertised by local browser processes."""
from pathlib import Path
import psutil

BROWSERS = {'chrome.exe','chrome','chromium.exe','chromium','msedge.exe','msedge','brave.exe','electron.exe'}
def option(args, name):
    for i, arg in enumerate(args):
        if arg.startswith(name+'='): return arg.split('=',1)[1]
        if arg == name and i+1<len(args): return args[i+1]
    return None

def discover_endpoints(processes=None):
    endpoints = {}
    for process in (psutil.process_iter(['name','cmdline']) if processes is None else processes):
        try:
            info = process.info
            if str(info.get('name','')).lower() not in BROWSERS: continue
            args = info.get('cmdline') or []
            if option(args,'--type'): continue
            value = option(args,'--remote-debugging-port')
            if value is None: continue
            port = int(value)
            if port == 0:
                folder = option(args,'--user-data-dir')
                if not folder: continue
                port = int((Path(folder)/'DevToolsActivePort').read_text().splitlines()[0])
            if 0 < port < 65536:
                endpoints[port] = {'endpoint':'http://127.0.0.1:'+str(port), 'browser':info['name']}
        except (psutil.Error, OSError, ValueError, IndexError): continue
    return [endpoints[p] for p in sorted(endpoints)]
