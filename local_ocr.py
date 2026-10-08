"""Offline OCR, cancellable process isolation and deterministic text matching."""
from difflib import SequenceMatcher
import json
import math
from pathlib import Path
import queue
import subprocess
import sys
import threading
import time
import unicodedata


class OcrCancelled(Exception):
    pass


class OcrSession:
    def __init__(self):
        self.process = None
        self.responses = queue.Queue(maxsize=2)
        self.reader = None

    def __enter__(self):
        return self

    def __exit__(self, *args):
        self.close()

    def _read(self, process):
        try:
            for line in process.stdout:
                self.responses.put(json.loads(line))
        except Exception as error:
            self.responses.put({'error': f'OCR进程通信失败：{error}'})

    def recognize(self, image, engine, config, context, timeout):
        if context.stop_requested:
            raise OcrCancelled()
        if self.process is None:
            root = Path(__file__).resolve().parent
            command = ([sys.executable, '--local-ocr-worker'] if getattr(sys, 'frozen', False)
                       else [sys.executable, str(root / 'local_ocr_worker.py')])
            self.process = subprocess.Popen(command, stdin=subprocess.PIPE, stdout=subprocess.PIPE,
                stderr=subprocess.DEVNULL, text=True, encoding='utf-8', bufsize=1,
                creationflags=subprocess.CREATE_NO_WINDOW if sys.platform == 'win32' else 0)
            self.reader = threading.Thread(target=self._read, args=(self.process,), daemon=True)
            self.reader.start()
        request = {'engine': engine, 'config': config, 'image': str(image)}
        self.process.stdin.write(json.dumps(request, ensure_ascii=True) + '\n')
        self.process.stdin.flush()
        deadline = time.monotonic() + timeout
        while True:
            if context.stop_requested:
                raise OcrCancelled()
            remaining = deadline - time.monotonic()
            if remaining <= 0:
                raise TimeoutError('本地OCR超时，已停止本次识别；可缩小区域或调高识别超时。')
            try:
                response = self.responses.get(timeout=min(.05, remaining))
            except queue.Empty:
                if self.process.poll() is not None:
                    raise RuntimeError('本地OCR进程异常退出；请检查模型、微信组件或运行库。')
                continue
            if 'error' in response:
                raise RuntimeError(response['error'])
            return response['rows']

    def close(self):
        process, self.process = self.process, None
        if process is None:
            return
        # Terminate only the helper and its own descendants, never user's WeChat.
        import psutil
        try:
            children = psutil.Process(process.pid).children(recursive=True)
        except psutil.Error:
            children = []
        if process.poll() is None:
            try:
                process.stdin.write('{"close":true}\n')
                process.stdin.flush()
                process.wait(timeout=.2)
            except (OSError, subprocess.TimeoutExpired):
                process.kill()
                process.wait(timeout=2)
        for child in children:
            try:
                child.kill()
            except psutil.Error:
                pass
        for stream in (process.stdin, process.stdout):
            stream.close()
        if self.reader is not None:
            self.reader.join(timeout=.2)


def normalized_text(text, ignore_case=True, ignore_spaces=True):
    value = unicodedata.normalize('NFKC', str(text))
    if ignore_case:
        value = value.casefold()
    return ''.join(value.split()) if ignore_spaces else value


def validated_rows(rows, offset=(0, 0), minimum_score=.5):
    """Screen coordinates are restored once, after recognizing the cropped image."""
    result = []
    for row in rows:
        score = float(row['score'])
        box = row['box']
        if len(box) != 4 or not math.isfinite(score) or not 0 <= score <= 1:
            raise ValueError('OCR返回了无效置信度或坐标框')
        points = [[float(p[0]) + offset[0], float(p[1]) + offset[1]] for p in box]
        if any(not math.isfinite(v) for p in points for v in p):
            raise ValueError('OCR返回了无效坐标')
        left, right = min(p[0] for p in points), max(p[0] for p in points)
        top, bottom = min(p[1] for p in points), max(p[1] for p in points)
        if right <= left or bottom <= top:
            raise ValueError('OCR返回了空坐标框')
        if score >= minimum_score:
            result.append({'text': str(row['text']), 'score': score, 'box': points,
                           'center': [round((left+right)/2), round((top+bottom)/2)]})
    return sorted(result, key=lambda r: (min(p[1] for p in r['box']), min(p[0] for p in r['box'])))


def find_matches(rows, target, mode, similarity=.8, ignore_case=True, ignore_spaces=True):
    target = normalized_text(target, ignore_case, ignore_spaces)
    if not target:
        raise ValueError('目标文字不能为空')
    found = []
    for row in rows:
        text = normalized_text(row['text'], ignore_case, ignore_spaces)
        score = SequenceMatcher(None, target, text, autojunk=False).ratio()
        matched = (text == target if mode == '精准' else target in text if mode == '包含'
                   else score >= similarity if mode == '模糊' else False)
        if matched:
            found.append(dict(row, similarity=score))
    return found
