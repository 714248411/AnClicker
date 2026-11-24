"""Prepare Crawl4AI dependencies; use AnClicker bundled Electron for browsing."""
import os
import argparse
from pathlib import Path
import subprocess
import sys

ROOT = Path(__file__).resolve().parents[1]
RUNTIME = ROOT / '.local/runtimes/crawl4ai'

def main():
    parser = argparse.ArgumentParser(description='准备或修复网页抓取运行环境')
    parser.add_argument('--runtime', type=Path, default=Path(os.environ.get('ANCLICKER_CRAWL4AI_RUNTIME') or RUNTIME))
    args = parser.parse_args()
    runtime = args.runtime.resolve()
    python = runtime / 'venv' / ('Scripts/python.exe' if sys.platform == 'win32' else 'bin/python')
    if not python.is_file():
        subprocess.run([sys.executable, '-m', 'venv', str(runtime / 'venv')], check=True)
    environment = dict(os.environ)
    environment.pop('PYTHONPATH', None)
    environment.pop('PYTHONHOME', None)
    subprocess.run([str(python), '-m', 'ensurepip', '--upgrade'], env=environment, check=True)
    subprocess.run([str(python), '-m', 'pip', 'install', '-r', str(ROOT / 'integrations/crawl4ai/requirements.txt')], env=environment, check=True)
    subprocess.run([str(python), '-c', 'from crawl4ai import AsyncWebCrawler; from playwright.async_api import async_playwright'], env=environment, check=True)
    print('使用 AnClicker 自带浏览器，无需安装本机 Chrome 或额外 Chromium。')
    print('网页抓取工具已准备：' + str(runtime))

if __name__ == '__main__':
    main()
