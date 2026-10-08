"""Isolated offline OCR host. No Qt, cloud client or runtime model downloads."""
import contextlib
import json
import os
from pathlib import Path
import sys


def discover_wechat_paths():
    """Only inspect conventional install/plugin paths; never download components."""
    if sys.platform == 'linux':
        return {'微信OCR路径': '/opt/wechat/wxocr', '微信运行目录': '/opt/wechat'} if Path('/opt/wechat/wxocr').is_file() else {}
    if sys.platform != 'win32':
        return {}
    appdata = Path(os.environ.get('APPDATA', ''))
    plugins = []
    for product in ('WeChat', 'xwechat'):
        root = appdata / 'Tencent' / product / 'XPlugin' / 'Plugins' / 'WeChatOCR'
        for name in ('wxocr.dll', 'WeChatOCR.exe'):
            plugins.extend(root.glob('*/extracted/' + name))
    bases = [Path(os.environ[key]) / 'Tencent' / product
             for key in ('ProgramFiles', 'ProgramFiles(x86)') if os.environ.get(key)
             for product in ('WeChat', 'Weixin')]
    try:
        import winreg
        for product in ('WeChat', 'Weixin'):
            for hive in (winreg.HKEY_CURRENT_USER, winreg.HKEY_LOCAL_MACHINE):
                try:
                    with winreg.OpenKey(hive, 'Software\\Tencent\\' + product) as key:
                        bases.append(Path(winreg.QueryValueEx(key, 'InstallPath')[0]))
                except OSError:
                    pass
    except ImportError:
        pass
    runtimes = [path.parent for base in bases for pattern in ('mmmojo*.dll', '*/mmmojo*.dll')
                for path in base.glob(pattern)]
    result = {}
    if plugins:
        result['微信OCR路径'] = str(max(plugins, key=lambda p: p.stat().st_mtime))
    if runtimes:
        result['微信运行目录'] = str(max(runtimes, key=lambda p: p.stat().st_mtime))
    return result


class RapidBackend:
    def __init__(self):
        from rapidocr_onnxruntime import RapidOCR
        root = Path(__file__).resolve().parent / 'ocr_models' / 'rapidocr'
        models = ('ch_PP-OCRv4_det_infer.onnx',
                  'ch_ppocr_mobile_v2.0_cls_infer.onnx', 'ch_PP-OCRv4_rec_infer.onnx')
        if any(not (root / name).is_file() for name in models):
            raise RuntimeError('RapidOCR 离线模型不完整，请恢复 ocr_models/rapidocr 文件夹；不会联网下载模型。')
        self.engine = RapidOCR(intra_op_num_threads=2, inter_op_num_threads=1,
                               det_model_path=str(root/models[0]), cls_model_path=str(root/models[1]),
                               rec_model_path=str(root/models[2]))

    def recognize(self, path):
        result, _ = self.engine(path, text_score=0.0)
        return [{'text': str(text), 'score': float(score),
                 'box': [[float(x), float(y)] for x, y in box]}
                for box, text, score in (result or [])]

    def close(self):
        pass


class WeChatBackend:
    """Use only the portable project's extracted Windows OCR components."""
    def __init__(self, config):
        self.extracted = None
        if sys.platform != 'win32':
            raise RuntimeError('此微信离线组件仅支持 Windows；请使用 RapidOCR。')
        runtime = Path(__file__).resolve().parent / 'ocr_models' / 'wechat'
        required = ('WeChatOCR.exe', 'mmmojo_64.dll', 'Model/OCRDetFP32.xnet.nas',
                    'Model/OCRRecogFP32V1.1.0.26.xnet', 'Model/OCRParaDetV1.1.0.26.xnet')
        missing = [name for name in required if not (runtime / name).is_file()]
        if missing:
            raise RuntimeError('程序目录的微信离线组件不完整，请恢复 ocr_models/wechat。缺少：' + '、'.join(missing))
        from wxocr_client import WeChatOCREngine
        self.extracted = WeChatOCREngine(runtime_dir=str(runtime), timeout=float(config.get('识别超时', 30)))
        if not self.extracted.start():
            error = self.extracted.last_error
            self.extracted.stop()
            raise RuntimeError(error or '微信离线 OCR 启动失败')

    def recognize(self, path):
        if self.extracted is not None:
            rows = self.extracted.recognize_file(path)
            return [{'text': text, 'score': float(score),
                     'box': [[left, top], [right, top], [right, bottom], [left, bottom]]}
                    for text, score, (left, top, right, bottom) in rows]
        raise RuntimeError('微信离线 OCR 未初始化')

    def close(self):
        if self.extracted is not None:
            self.extracted.stop()


def normalize_wechat(result):
    if isinstance(result, str):
        result = json.loads(result)
    if not isinstance(result, dict) or not any(key in result for key in ('ocrResult', 'ocr_response')):
        raise ValueError('微信OCR结果格式不兼容：缺少文字框，未使用猜测坐标。')
    if result.get('errcode', 0):
        raise RuntimeError(f'微信OCR返回错误：{result["errcode"]}')
    rows = []
    for item in result.get('ocrResult', result.get('ocr_response', [])):
        rect = item.get('location', item)
        left, top, right, bottom = (float(rect[key]) for key in ('left', 'top', 'right', 'bottom'))
        rows.append({'text': str(item['text']), 'score': float(item.get('score', item.get('rate', 1))),
                     'box': [[left, top], [right, top], [right, bottom], [left, bottom]]})
    return rows


def main():
    # Windows --windowed bootloaders set Python standard streams to None even
    # when the parent supplied pipe handles. Recover those inherited handles.
    if sys.platform == 'win32' and (sys.stdin is None or sys.stdout is None):
        import ctypes
        import msvcrt
        kernel = ctypes.WinDLL('kernel32', use_last_error=True)
        kernel.GetStdHandle.argtypes = [ctypes.c_ulong]
        kernel.GetStdHandle.restype = ctypes.c_void_p
        for attr, number, flags, mode in (('stdin', -10, os.O_RDONLY, 'r'),
                                           ('stdout', -11, os.O_WRONLY, 'w')):
            if getattr(sys, attr) is None:
                handle = kernel.GetStdHandle(number & 0xffffffff)
                if not handle or handle == ctypes.c_void_p(-1).value:
                    raise RuntimeError('Missing inherited OCR pipe: ' + attr)
                descriptor = msvcrt.open_osfhandle(handle, flags)
                setattr(sys, attr, os.fdopen(descriptor, mode, encoding='utf-8', buffering=1))
    if sys.stderr is None:
        sys.stderr = open(os.devnull, 'w', encoding='utf-8')
    # Dedicated pipe: native libraries may print, so reserve the original stdout.
    output = sys.stdout
    backend = None
    try:
        for line in sys.stdin:
            try:
                request = json.loads(line)
                if request.get('close'):
                    break
                with contextlib.redirect_stdout(sys.stderr):
                    if backend is None:
                        backend = (RapidBackend() if request['engine'] == 'RapidOCR'
                                   else WeChatBackend(request['config']))
                    rows = [] if request.get('warmup') else backend.recognize(request['image'])
                response = {'rows': rows}
            except Exception as error:
                response = {'error': str(error) or type(error).__name__}
            output.write(json.dumps(response, ensure_ascii=True, allow_nan=False) + '\n')
            output.flush()
    finally:
        if backend is not None:
            with contextlib.redirect_stdout(sys.stderr):
                backend.close()


if __name__ == '__main__':
    main()
