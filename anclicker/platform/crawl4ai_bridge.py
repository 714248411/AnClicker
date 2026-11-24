"""Cancellable Crawl4AI subprocess shared by instructions and the Agent."""
import json
import os
import subprocess
import sys
import tempfile
import time
from pathlib import Path
import psutil
from anclicker.app.paths import runtime_path, resource_path
from anclicker.domain.web_urls import normalize_web_url
from anclicker.platform.crawl_browser import bundled_crawl_browser


def stop_process_tree(child):
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


def crawl_page(url, context=None, selector='', wait_for='', timeout=60, max_chars=20000):
    if context is not None and context.stop_requested:
        raise InterruptedError('已停止网页抓取')
    url = normalize_web_url(url)
    if type(timeout) is not int or not 5 <= timeout <= 180:
        raise ValueError('抓取超时必须在 5 到 180 秒之间')
    if type(max_chars) is not int or not 500 <= max_chars <= 200000:
        raise ValueError('最大字符数必须在 500 到 200000 之间')
    if not isinstance(selector, str) or not isinstance(wait_for, str) or max(len(selector), len(wait_for)) > 2000:
        raise ValueError('CSS 选择器无效或过长')
    runtime = Path(os.environ.get('ANCLICKER_CRAWL4AI_RUNTIME') or runtime_path('crawl4ai'))
    portable = runtime / 'python' / ('python.exe' if sys.platform == 'win32' else 'bin/python3')
    default_python = portable if portable.is_file() else runtime / 'venv' / ('Scripts/python.exe' if sys.platform == 'win32' else 'bin/python')
    executable = Path(os.environ.get('ANCLICKER_CRAWL4AI_PYTHON') or default_python)
    if not executable.is_file():
        raise RuntimeError('未找到网页抓取运行环境。请在程序目录双击“准备网页抓取工具.cmd”，安装完成后重试；首次准备需要联网。')
    environment = dict(os.environ)
    environment.pop('PYTHONPATH', None)
    environment.pop('PYTHONHOME', None)
    environment['PYTHONIOENCODING'] = 'utf-8'
    environment['PLAYWRIGHT_BROWSERS_PATH'] = str(runtime / 'browsers')
    from anclicker.app.paths import TEMP_FOLDER
    environment['CRAWL4_AI_BASE_DIRECTORY'] = str(Path(TEMP_FOLDER) / 'crawl4ai')
    environment['PYTHONNOUSERSITE'] = '1'
    worker = resource_path('integrations/crawl4ai/worker.py')
    if not worker.is_file():
        raise RuntimeError('网页抓取组件文件缺失，请重新解压完整程序包。')
    request = dict(url=url, selector=selector, wait_for=wait_for, timeout=timeout, max_chars=max_chars)
    with tempfile.TemporaryDirectory(prefix='anclicker-crawl-') as directory, bundled_crawl_browser(directory, context) as cdp_url:
        request['cdp_url'] = cdp_url
        folder = Path(directory)
        source, target = folder / 'request.json', folder / 'result.json'
        source.write_text(json.dumps(request, ensure_ascii=False), encoding='utf-8')
        with (folder / 'worker.log').open('wb') as log:
            child = subprocess.Popen([str(executable), str(worker), str(source), str(target)],
                cwd=folder, env=environment, stdin=subprocess.DEVNULL, stdout=log, stderr=log,
                creationflags=getattr(subprocess, 'CREATE_NO_WINDOW', 0))
            deadline = time.monotonic() + timeout + 30
            try:
                while child.poll() is None:
                    if context is not None and context.stop_requested:
                        raise InterruptedError('已停止网页抓取')
                    if time.monotonic() >= deadline:
                        raise TimeoutError('网页抓取超时，已关闭抓取进程')
                    time.sleep(.1)
                if context is not None and context.stop_requested:
                    raise InterruptedError('已停止网页抓取')
                if not target.is_file():
                    raise RuntimeError('网页抓取进程启动失败（退出码 ' + str(child.returncode) + '），请运行“准备网页抓取工具.cmd”修复环境。')
                response = json.loads(target.read_text(encoding='utf-8'))
                if not response.get('ok'):
                    raise RuntimeError('网页抓取失败：' + str(response.get('error', '未知错误')))
                return response['result']
            finally:
                if child.poll() is None:
                    stop_process_tree(child)
