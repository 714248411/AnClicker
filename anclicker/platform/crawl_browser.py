"""Run an isolated hidden instance of AnClicker's bundled Electron browser."""
from contextlib import contextmanager
from pathlib import Path
import os
import subprocess
import sys
import time
import psutil
from anclicker.app.paths import resource_path, runtime_path


@contextmanager
def bundled_crawl_browser(folder, context=None):
    entry = 'Electron.app/Contents/MacOS/Electron' if sys.platform == 'darwin' else 'electron.exe' if sys.platform == 'win32' else 'electron'
    executable = runtime_path('electron') / entry
    script = resource_path('integrations/crawl4ai/browser.js')
    if not executable.is_file() or not script.is_file():
        raise RuntimeError('AnClicker 自带浏览器组件缺失，请重新解压完整程序包。')
    profile = Path(folder) / 'browser-profile'
    profile.mkdir()
    environment = dict(os.environ)
    environment.pop('ELECTRON_RUN_AS_NODE', None)
    with (Path(folder) / 'browser.log').open('wb') as log:
        child = subprocess.Popen([str(executable), str(script), str(profile)], env=environment,
            stdin=subprocess.DEVNULL, stdout=log, stderr=log,
            creationflags=getattr(subprocess, 'CREATE_NO_WINDOW', 0))
        try:
            deadline = time.monotonic()+25
            port_file = profile / 'DevToolsActivePort'
            while True:
                if context is not None and context.stop_requested:
                    raise InterruptedError('已停止网页抓取')
                if child.poll() is not None:
                    raise RuntimeError('AnClicker 自带浏览器启动失败，请检查浏览器组件是否完整。')
                try:
                    port = int(port_file.read_text().splitlines()[0])
                    if 0 < port < 65536:
                        break
                except (OSError, ValueError, IndexError):
                    pass
                if time.monotonic() >= deadline:
                    raise TimeoutError('AnClicker 自带浏览器启动超时')
                time.sleep(.1)
            yield 'http://127.0.0.1:' + str(port)
        finally:
            try:
                process = psutil.Process(child.pid)
                descendants = process.children(recursive=True)
                for item in reversed(descendants):
                    try: item.kill()
                    except psutil.NoSuchProcess: pass
                try: process.kill()
                except psutil.NoSuchProcess: pass
                psutil.wait_procs(descendants, timeout=3)
            except psutil.NoSuchProcess:
                pass
            child.wait(timeout=5)
