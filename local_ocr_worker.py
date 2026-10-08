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
        import rapidocr_onnxruntime
        from rapidocr_onnxruntime import RapidOCR
        root = Path(rapidocr_onnxruntime.__file__).parent
        models = ('ch_PP-OCRv4_det_infer.onnx',
                  'ch_ppocr_mobile_v2.0_cls_infer.onnx', 'ch_PP-OCRv4_rec_infer.onnx')
        if any(not (root / 'models' / name).is_file() for name in models):
            raise RuntimeError('RapidOCR 离线模型不完整，请完整安装/解压软件包；不会联网下载模型。')
        self.engine = RapidOCR(intra_op_num_threads=2, inter_op_num_threads=1)

    def recognize(self, path):
        result, _ = self.engine(path, text_score=0.0)
        return [{'text': str(text), 'score': float(score),
                 'box': [[float(x), float(y)] for x, y in box]}
                for box, text, score in (result or [])]

    def close(self):
        pass


class WeChatBackend:
    """Local WeChat 3.x adapter; 4.x uses the optional wcocr Python extension."""
    def __init__(self, config):
        import threading
        self.manager = None
        self.event = threading.Event()
        self.result = None
        detected = discover_wechat_paths() if not config.get('微信OCR路径') or not config.get('微信运行目录') else {}
        binary = config.get('微信OCR路径') or detected.get('微信OCR路径', '')
        runtime = config.get('微信运行目录') or detected.get('微信运行目录', '')
        if not binary or not runtime or not Path(binary).is_file() or not Path(runtime).is_dir():
            raise RuntimeError('请设置本机微信OCR文件路径和微信运行目录；不会下载或分发微信私有组件。')
        extension = config.get('微信接口目录', '')
        if extension:
            sys.path.insert(0, str(Path(extension).resolve()))
        self.wcocr = None
        try:
            import wcocr
        except ImportError:
            wcocr = None
        if wcocr is not None:
            self.wcocr = wcocr
            if wcocr.init(binary, runtime) is False:
                raise RuntimeError('微信 OCR 初始化失败，请检查组件版本与位数。')
        else:
            if sys.platform != 'win32' or Path(binary).suffix.lower() != '.exe':
                raise RuntimeError('微信4.x/Linux需要匹配当前Python与系统的wcocr接口，请设置微信接口目录。')
            try:
                from wechat_ocr.ocr_manager import OcrManager
            except ImportError as error:
                raise RuntimeError('缺少微信OCR接口，请安装 requirements-ocr-wechat.txt 或配置 wcocr 接口目录。') from error
            self.manager = OcrManager(runtime)
            self.manager.SetExePath(binary)
            self.manager.SetUsrLibDir(runtime)
            self.manager.SetOcrResultCallback(self._result)
            self.manager.StartWeChatOCR()

    def _result(self, path, result):
        self.result = result
        self.event.set()

    def recognize(self, path):
        if self.wcocr is not None:
            result = self.wcocr.ocr(path)
        else:
            self.event.clear()
            self.manager.DoOCRTask(path)
            if not self.event.wait(60):
                raise TimeoutError('微信OCR没有返回识别结果')
            result = self.result
        return normalize_wechat(result)

    def close(self):
        if self.manager is not None:
            self.manager.KillWeChatOCR()


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
                    rows = backend.recognize(request['image'])
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
