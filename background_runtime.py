"""Per-execution background window ownership and dm input/screenshot adapter."""
from collections import namedtuple
from contextlib import contextmanager
from contextvars import ContextVar
import json
import os
import shutil
from pathlib import Path
from queue import Queue, Empty
import subprocess
import sys
import tempfile
import threading
import time

_context = ContextVar('anclicker_input_context', default=None)
Point = namedtuple('Point', 'x y')
Size = namedtuple('Size', 'width height')
SESSION = '_background_session'
ERROR = '_background_error'
_pending_host_cleanup = set()
_cleanup_lock = threading.Lock()
_cleanup_running = False


def release_host_directory(directory):
    """DX helper DLLs may remain mapped briefly after UnBindWindow."""
    path = Path(directory.name).resolve()
    if path.parent != Path(tempfile.gettempdir()).resolve() or not path.name.startswith('anclicker-dm-host-') or path.is_symlink():
        return
    try:
        directory.cleanup()
    except OSError:
        pass
    if not path.exists():
        return
    global _cleanup_running
    with _cleanup_lock:
        _pending_host_cleanup.add(path)
        if _cleanup_running:
            return
        _cleanup_running = True
    def retry():
        global _cleanup_running
        try:
            for _ in range(30):
                time.sleep(1)
                with _cleanup_lock:
                    paths = tuple(_pending_host_cleanup)
                for candidate in paths:
                    # Only exact temporary directories created by this process are queued.
                    if candidate.parent == Path(tempfile.gettempdir()).resolve() and not candidate.is_symlink():
                        shutil.rmtree(candidate, ignore_errors=True)
                    if not candidate.exists():
                        with _cleanup_lock:
                            _pending_host_cleanup.discard(candidate)
                with _cleanup_lock:
                    if not _pending_host_cleanup:
                        break
        finally:
            with _cleanup_lock:
                _cleanup_running = False
    threading.Thread(target=retry, name='dm-temp-cleanup', daemon=True).start()


@contextmanager
def input_context(context):
    token = _context.set(context)
    try:
        yield
    finally:
        _context.reset(token)


def current_backend(context=None):
    context = context if context is not None else _context.get()
    if context is None:
        return None
    if context.metadata.get(ERROR):
        raise RuntimeError(context.metadata[ERROR])
    return context.metadata.get(SESSION)


class Windows:
    def __init__(self):
        if sys.platform != 'win32':
            raise RuntimeError('大漠后台功能仅支持 Windows')
        import win32gui
        import win32process
        self.gui, self.process = win32gui, win32process

    def describe(self, hwnd):
        if not hwnd or not self.gui.IsWindow(hwnd):
            raise RuntimeError('目标窗口已关闭，请重新选择窗口')
        pid = self.process.GetWindowThreadProcessId(hwnd)[1]
        import psutil
        try:
            executable = psutil.Process(pid).exe()
        except (psutil.Error, OSError):
            executable = ''
        return {'窗口句柄': str(hwnd), '窗口标题': self.gui.GetWindowText(hwnd),
                '窗口类名': self.gui.GetClassName(hwnd), '进程路径': executable, '进程ID': pid}

    def enumerate(self, children=False):
        found = []
        def visit(hwnd, _):
            try:
                item = self.describe(hwnd)
                rect = self.gui.GetClientRect(hwnd)
                if (item['进程ID'] != os.getpid() and self.gui.IsWindowVisible(hwnd)
                        and rect[2] > 0 and rect[3] > 0):
                    found.append(item)
            except (OSError, RuntimeError, self.gui.error):
                pass
        self.gui.EnumWindows(visit, None)
        if children:
            for item in list(found):
                self.gui.EnumChildWindows(int(item['窗口句柄']), visit, None)
        return found

    def at_point(self, point, *, child=False):
        hwnd = self.gui.WindowFromPoint(tuple(map(int, point)))
        if hwnd and not child:
            hwnd = self.gui.GetAncestor(hwnd, 2)  # GA_ROOT: target application, not its label/button.
        target = self.describe(hwnd)
        if target['进程ID'] == os.getpid():
            raise RuntimeError('请选择 AnClicker 以外的目标窗口')
        if target['窗口类名'] in ('Progman', 'WorkerW', 'Shell_TrayWnd', 'Shell_SecondaryTrayWnd'):
            raise RuntimeError('请点击应用窗口，不能选择桌面或任务栏')
        self.size(target)
        return target

    def cursor_position(self):
        return self.gui.GetCursorPos()

    def resolve(self, parameters):
        def identity(item):
            return all(not parameters.get(key) or str(item[key]).casefold() == str(parameters[key]).casefold()
                       for key in ('窗口标题', '窗口类名', '进程路径'))
        try:
            hwnd = int(str(parameters.get('窗口句柄', '0')), 0)
            item = self.describe(hwnd)
            if identity(item) and (not parameters.get('进程ID') or item['进程ID'] == int(parameters['进程ID'])):
                if item['进程ID'] == os.getpid():
                    raise RuntimeError('不能绑定 AnClicker 自身窗口')
                return item
        except (ValueError, RuntimeError, OSError):
            pass
        if not any(parameters.get(key) for key in ('窗口标题', '窗口类名', '进程路径')):
            raise RuntimeError('未找到目标窗口，请重新选择窗口')
        matches = [item for item in self.enumerate(children=True) if identity(item)]
        if len(matches) != 1:
            raise RuntimeError('存在多个匹配窗口，请重新选择窗口' if matches else '未找到目标窗口，请先打开并重新选择窗口')
        return matches[0]

    def validate(self, target):
        hwnd = int(target['窗口句柄'])
        if (not self.gui.IsWindow(hwnd) or self.process.GetWindowThreadProcessId(hwnd)[1] != target['进程ID']
                or self.gui.GetClassName(hwnd) != target['窗口类名']):
            raise RuntimeError('绑定窗口已关闭或已被替换，请重新绑定；已阻止前台操作')

    def size(self, target):
        self.validate(target)
        rect = self.gui.GetClientRect(int(target['窗口句柄']))
        if rect[2] <= 0 or rect[3] <= 0:
            raise RuntimeError('绑定窗口没有可用的内容区域')
        return Size(rect[2], rect[3])


class DmTransport:
    """A DLL crash/time-out must not take down the editor or redirect desktop input."""
    def __init__(self, context):
        self.context = context
        self._host_dir = None
        env = dict(os.environ, PYTHONUTF8='1')
        from background_component_auto import resolved_config
        # A supplied worker/DLL is authoritative; do not download a replacement.
        explicit = any(env.get(key, '').strip() for key in (
            'ANCLICKER_DM_DLL', 'ANCLICKER_DM_BACKEND', 'ANCLICKER_DM_PYTHON'))
        config = resolved_config(automatic=not explicit,
            emit=context.emit, cancelled=lambda: context.stop_requested)
        for name, key in (('dll_path', 'ANCLICKER_DM_DLL'), ('reg_code', 'ANCLICKER_DM_REG_CODE'),
                          ('reg_extra', 'ANCLICKER_DM_REG_EXTRA'), ('backend', 'ANCLICKER_DM_BACKEND'),
                          ('helper_path', 'ANCLICKER_DM_HELPER')):
            if config.get(name):
                env.setdefault(key, str(config[name]))
        if env.get('ANCLICKER_DM_BACKEND') == 'native-7.2424':
            self.capabilities = set(json.loads(Path(__file__).with_name('background_native_72424.json').read_text(encoding='utf8'))['methods']) | {'CaptureArray'}
        else:
            from background_catalog import METHODS
            self.capabilities = set(METHODS)
        runtime = os.environ.get('ANCLICKER_DM_PYTHON', '').strip()
        script = str(Path(__file__).with_name('background_dm_worker.py'))
        command = [runtime, '-u', script] if runtime else (
            [sys.executable, '--background-dm-worker'] if getattr(sys, 'frozen', False)
            else [sys.executable, '-u', script])
        if env.get('ANCLICKER_DM_DLL'):
            from background_dm_worker import pe_bits
            dll = Path(env['ANCLICKER_DM_DLL'])
            if pe_bits(dll) == 32:
                self._host_dir = tempfile.TemporaryDirectory(prefix='anclicker-dm-host-', ignore_cleanup_errors=True)
                host = Path(self._host_dir.name)
                host_dll = host / ('xd47243.dll' if env.get('ANCLICKER_DM_BACKEND') == 'native-7.2424' else 'dm.dll')
                shutil.copyfile(dll, host_dll)
                if env.get('ANCLICKER_DM_BACKEND') == 'native-7.2424':
                    helper = Path(env.get('ANCLICKER_DM_HELPER', ''))
                    if not helper.is_file():
                        self._host_dir.cleanup()
                        raise RuntimeError('未找到匹配的后台组件辅助库')
                    shutil.copyfile(helper, host / 'Go.dll')
                    env['ANCLICKER_DM_HELPER'] = str(host / 'Go.dll')
                manifest = ('<?xml version="1.0" encoding="UTF-8" standalone="yes"?>'
                    '<assembly xmlns="urn:schemas-microsoft-com:asm.v1" manifestVersion="1.0">'
                    '<assemblyIdentity type="win32" name="AnClicker.DmHost" version="1.0.0.0" processorArchitecture="x86"/>'
                    '<file name="dm.dll"><comClass clsid="{26037A0E-7CBD-4FFF-9C63-56F2D0770214}" '
                    'threadingModel="Both" progid="dm.dmsoft" tlbid="{84288AAD-BA02-4EF2-85EC-3FAD4D11354D}"/>'
                    '<typelib tlbid="{84288AAD-BA02-4EF2-85EC-3FAD4D11354D}" version="1.0" helpdir=""/></file></assembly>')
                (host / 'dm.manifest').write_text(manifest, encoding='utf-8')
                env['ANCLICKER_DM_DLL'] = str(host_dll)
                env['ANCLICKER_DM_MANIFEST'] = str(host / 'dm.manifest')
                powershell = Path(env.get('WINDIR', r'C:\Windows')) / 'SysWOW64/WindowsPowerShell/v1.0/powershell.exe'
                if not powershell.is_file():
                    powershell = Path(env.get('WINDIR', r'C:\Windows')) / 'System32/WindowsPowerShell/v1.0/powershell.exe'
                command = [str(powershell), '-NoProfile', '-NonInteractive', '-ExecutionPolicy', 'Bypass',
                           '-File', str(Path(__file__).with_name('background_dm_host.ps1'))]
        try:
            self.process = subprocess.Popen(command, stdin=subprocess.PIPE, stdout=subprocess.PIPE,
                stderr=subprocess.DEVNULL, text=True, encoding='utf-8', bufsize=1,
                env=env, creationflags=getattr(subprocess, 'CREATE_NO_WINDOW', 0))
        except Exception:
            if self._host_dir is not None:
                self._host_dir.cleanup()
            raise
        self.responses = Queue()
        def read():
            try:
                for line in self.process.stdout:
                    self.responses.put(line)
            finally:
                self.responses.put(None)
        self.reader = threading.Thread(target=read, daemon=True)
        self.reader.start()
        try:
            self.version = self.call('init')
        except Exception:
            self.close()
            raise

    def call(self, method, *args, cleanup=False, raw=False):
        if self.process.poll() is not None:
            raise RuntimeError('大漠后台进程已退出，请检查插件安装、位数及授权后重新绑定')
        try:
            self.process.stdin.write(json.dumps({'method': method, 'args': args, 'raw': raw}, ensure_ascii=True) + '\n')
            self.process.stdin.flush()
        except (OSError, ValueError) as exc:
            raise RuntimeError('大漠后台连接已断开') from exc
        deadline = time.monotonic() + (2 if cleanup else 30)
        while True:
            if not cleanup and self.context.stop_requested:
                self.close()
                raise RuntimeError('后台操作已取消')
            try:
                line = self.responses.get(timeout=.05)
                if line is None:
                    raise RuntimeError('大漠后台进程异常退出，请检查插件安装、位数及授权')
                result = json.loads(line)
                if not result['ok']:
                    raise RuntimeError(result['error'])
                return result['result']
            except Empty:
                if time.monotonic() >= deadline:
                    self.close()
                    raise RuntimeError('大漠后台调用超时，已结束后台进程')

    def close(self):
        # Closing stdin lets the host release native objects on their owning thread.
        try:
            self.process.stdin.close()
        except (OSError, ValueError):
            pass
        try:
            self.process.wait(timeout=2)
        except subprocess.TimeoutExpired:
            self.process.terminate()
            try:
                self.process.wait(timeout=2)
            except subprocess.TimeoutExpired:
                self.process.kill()
                self.process.wait(timeout=2)
        self.reader.join(timeout=1)
        self.process.stdout.close()
        if self._host_dir is not None:
            release_host_directory(self._host_dir)
            self._host_dir = None


class BackgroundInput:
    is_background = True
    FAILSAFE = False

    def __init__(self, context, windows, target, transport):
        self.context, self.windows, self.target, self.transport = context, windows, target, transport
        self.hwnd = int(target['窗口句柄'])
        self._position = Point(0, 0)
        self.keys, self.buttons = set(), set()
        self.closed = False
        self.directory = tempfile.TemporaryDirectory(prefix='anclicker-background-')

    def _call(self, method, *args, cleanup=False):
        if self.closed:
            raise RuntimeError('后台窗口已经解除绑定')
        if not cleanup:
            self.windows.validate(self.target)
        return self.transport.call(method, *args, cleanup=cleanup)

    def failSafeCheck(self):
        self.windows.validate(self.target)

    def size(self):
        return self.windows.size(self.target)

    def position(self):
        self.failSafeCheck()
        return self._position

    def _point(self, x, y):
        x, y = int(x), int(y)
        width, height = self.size()
        if not (0 <= x < width and 0 <= y < height):
            raise ValueError(f'坐标 {x},{y} 超出绑定窗口内容区 {width}×{height}；请使用窗口内坐标')
        return x, y

    def _wait(self, seconds):
        from instructions.common.actions import wait_interruptibly
        if not wait_interruptibly(self.context, float(seconds)):
            raise RuntimeError('后台操作已停止')

    def moveTo(self, x, y, duration=0, **kwargs):
        x, y = self._point(x, y)
        start = self._position
        steps = max(1, min(500, int(float(duration) / .02)))
        for step in range(1, steps + 1):
            self._wait(float(duration) / steps)
            px, py = round(start.x + (x-start.x)*step/steps), round(start.y + (y-start.y)*step/steps)
            self._call('MoveTo', px, py)
            self._position = Point(px, py)

    def moveRel(self, x, y, duration=0, **kwargs):
        self.moveTo(self._position.x+x, self._position.y+y, duration, **kwargs)

    @staticmethod
    def _button(button):
        try:
            return {'left': 'Left', 'right': 'Right', 'middle': 'Middle'}[button]
        except KeyError:
            raise ValueError(f'大漠后台暂不支持鼠标按键：{button}')

    def click(self, x=None, y=None, clicks=1, interval=0, button='left', **kwargs):
        prefix = self._button(button)
        if x is not None and y is not None:
            self.moveTo(x, y)
        for index in range(int(clicks)):
            self._wait(interval if index else 0)
            self._call(prefix+'Click')

    def mouseDown(self, x=None, y=None, button='left', **kwargs):
        prefix = self._button(button)
        if x is not None and y is not None:
            self.moveTo(x, y)
        self.buttons.add(button)
        self._call(prefix+'Down')

    def mouseUp(self, x=None, y=None, button='left', **kwargs):
        self._call(self._button(button)+'Up', cleanup=True)
        self.buttons.discard(button)

    @staticmethod
    def _key(key):
        key = str(key).lower()
        if key.startswith('win32:'):
            vk = int(key.split(':')[1])
            if not 1 <= vk <= 255 or vk == 231:
                raise ValueError('后台不支持此录制字符键，请使用文本输入指令')
            return vk
        if key.startswith('native:win32:'):
            return int(key.rsplit(':', 1)[1])
        key = key.removeprefix('special:').removeprefix('char:')
        aliases = {'enter':13, 'return':13, 'tab':9, 'space':32, 'esc':27, 'escape':27,
                   'backspace':8, 'delete':46, 'insert':45, 'home':36, 'end':35,
                   'pageup':33, 'pagedown':34, 'up':38, 'down':40, 'left':37, 'right':39,
                   'shift':16, 'ctrl':17, 'control':17, 'alt':18, 'win':91, 'winleft':91,
                   'winright':92, 'capslock':20, 'numlock':144, 'scrolllock':145,
                   'pause':19, 'printscreen':44, 'ctrlleft':162, 'ctrlright':163,
                   'shiftleft':160, 'shiftright':161, 'altleft':164, 'altright':165}
        key = {'ctrl_l':'ctrlleft', 'ctrl_r':'ctrlright', 'shift_l':'shiftleft', 'shift_r':'shiftright',
               'alt_l':'altleft', 'alt_r':'altright', 'cmd':'win', 'cmd_l':'winleft', 'cmd_r':'winright',
               'page_up':'pageup', 'page_down':'pagedown', 'caps_lock':'capslock'}.get(key, key)
        aliases.update({'-':189, '=':187, '[':219, ']':221, ';':186, "'":222,
                        ',':188, '.':190, '/':191, '\\':220, '`':192})
        if key in aliases:
            return aliases[key]
        if len(key) == 1 and key.isascii() and key.isalnum():
            return ord(key.upper())
        if key.startswith('f') and key[1:].isdigit() and 1 <= int(key[1:]) <= 24:
            return 111 + int(key[1:])
        raise ValueError(f'后台不支持此按键名称：{key}，文字请使用文本输入指令')

    def keyDown(self, key, **kwargs):
        vk = self._key(key)
        self.keys.add(vk)
        self._call('KeyDown', vk)

    def keyUp(self, key, **kwargs):
        vk = self._key(key)
        self._call('KeyUp', vk, cleanup=True)
        self.keys.discard(vk)

    def hotkey(self, *keys, **kwargs):
        pressed = []
        try:
            for key in keys:
                pressed.append(key)
                self.keyDown(key)
        finally:
            for key in reversed(pressed):
                self.keyUp(key)

    def write(self, text, **kwargs):
        self._call('SendString', self.hwnd, str(text))

    def scroll(self, clicks, **kwargs):
        if not float(clicks).is_integer():
            raise ValueError('后台滚轮必须为整数步数')
        for _ in range(abs(int(clicks))):
            self._wait(0)
            self._call('WheelUp' if clicks > 0 else 'WheelDown')

    def require_capture(self):
        if not getattr(self, 'capture_enabled', True):
            raise RuntimeError('当前绑定仅启用后台键鼠；请在“绑定选择窗口”中开启截图 / 识图 / 取色后重新绑定')

    def screenshot(self, region=None, **kwargs):
        self.require_capture()
        from PIL import Image
        width, height = self.size()
        x, y, w, h = (0, 0, width, height) if region is None else tuple(map(int, region))
        if w <= 0 or h <= 0:
            raise ValueError('截图区域宽高必须大于零')
        self._point(x, y)
        self._point(x+w-1, y+h-1)
        path = str(Path(self.directory.name) / 'capture.bmp')
        Path(path).unlink(missing_ok=True)
        self._call('Capture', x, y, x+w, y+h, path)
        with Image.open(path) as image:
            result = image.convert('RGB').copy()
        if result.size != (w, h):
            raise RuntimeError('后台截图尺寸异常，请检查窗口状态和图像模式')
        return result

    def pixel(self, x, y):
        self.require_capture()
        value = str(self._call('GetColor', *self._point(x, y))).strip()
        if len(value) != 6:
            raise RuntimeError('后台取色失败，请检查图像绑定模式')
        return tuple(int(value[i:i+2], 16) for i in (0, 2, 4))

    def close(self, keep_transport=False):
        if self.closed:
            return False
        released = False
        try:
            for value in list(self.keys):
                try:
                    self._call('KeyUp', value, cleanup=True)
                except Exception:
                    pass
            for button in self.buttons:
                try:
                    self._call(self._button(button)+'Up', cleanup=True)
                except Exception:
                    pass
            try:
                released = self._call('UnBindWindow', cleanup=True) == 1
            except Exception:
                pass
        finally:
            self.closed = True
            try:
                if not keep_transport or not released:
                    self.transport.close()
            finally:
                self.directory.cleanup()
        return keep_transport and released


def close_background(context):
    context.metadata.pop('background_binding_profiles', None)
    session = context.metadata.pop(SESSION, None)
    context.metadata.pop(ERROR, None)
    if session is not None:
        context.metadata.pop('recorded_keys', None)
        context.metadata.pop('recorded_buttons', None)
        session.close()


def bind_background(context, parameters):
    from background_binding import binding_attempts, selected_preset, capture_enabled, AUTO
    existing = context.metadata.get(SESSION)
    windows = (context.service('background_windows') or Windows)()
    try:
        if context.stop_requested:
            raise RuntimeError('后台绑定已取消')
        attempts, delay = binding_attempts(parameters)
        capture = capture_enabled(parameters)
        target = windows.resolve(parameters)
        signature = (tuple((key, target.get(key)) for key in ('窗口句柄', '进程ID', '窗口类名', '进程路径')),
                     tuple(attempts), capture)
        if (existing is not None and not existing.closed
                and getattr(existing, 'binding_signature', None) == signature
                and not existing.keys and not existing.buttons
                and not context.metadata.get('recorded_keys') and not context.metadata.get('recorded_buttons')):
            windows.validate(target)
            process = getattr(existing.transport, 'process', None)
            if process is None or process.poll() is None:
                context.emit('已复用当前有效后台绑定，无需重复初始化')
                return existing.hwnd
    except Exception:
        close_background(context)
        context.metadata[ERROR] = '后台窗口尚未成功绑定，已阻止前台操作；请重新绑定或明确解除绑定'
        raise
    profiles = context.metadata.get('background_binding_profiles', {})
    close_background(context)
    context.metadata[ERROR] = '后台窗口尚未成功绑定，已阻止前台操作；请重新绑定或明确解除绑定'
    context.metadata['background_binding_profiles'] = profiles
    if selected_preset(parameters) == AUTO and signature in profiles:
        preferred = profiles[signature]
        attempts.sort(key=lambda item: item[0] != preferred)
    transport = None
    started = time.monotonic()
    for index, (profile, display, mouse, keyboard, mode) in enumerate(attempts):
        try:
            windows.validate(target)
        except Exception:
            if transport is not None:
                transport.close()
            raise
        if transport is None:
            factory = context.service('background_transport')
            if factory is not None:
                transport = factory(context)
            else:
                from background_preload import take_preloaded
                transport = take_preloaded(context) or DmTransport(context)
        session = BackgroundInput(context, windows, target, transport)
        session.capture_enabled = capture
        bound = False
        try:
            result = session._call('BindWindow', session.hwnd, display, mouse, keyboard, mode)
            if result != 1:
                raise RuntimeError('组件返回绑定失败')
            bound = True
            session._wait(delay)
            if selected_preset(parameters) == AUTO and capture:
                session.screenshot()
        except Exception as error:
            profiles.pop(signature, None)
            reuse = bound and index + 1 < len(attempts) and not context.stop_requested
            if not session.close(keep_transport=reuse):
                transport = None
            if context.stop_requested:
                raise RuntimeError('后台绑定已取消') from error
            if index + 1 == len(attempts):
                raise RuntimeError('后台绑定失败（' + ' → '.join(item[0] for item in attempts) +
                    '）：' + str(error) + '；可尝试 GDI 兼容方案或重新选择窗口') from error
            context.emit(profile + ' 未就绪：' + str(error) + '；正在尝试 ' + attempts[index + 1][0])
            continue
        session.binding_profile = profile
        session.binding_signature = signature
        profiles[signature] = profile
        while len(profiles) > 16:
            profiles.pop(next(iter(profiles)))
        context.metadata[SESSION] = session
        context.metadata.pop(ERROR, None)
        context.emit(f"后台窗口已绑定：{target['窗口标题'] or target['窗口类名']}；方案 {profile}；用时 {time.monotonic()-started:.2f} 秒；后续操作使用窗口内容区坐标")
        return session.hwnd


def execute_background_method(context, group, parameters):
    from background_catalog import METHODS, method_name, values_for
    from instructions.common.actions import substitute_variables
    name = method_name(parameters['接口'])
    definition = METHODS.get(name)
    if definition is None or definition['group'] != group:
        raise ValueError('后台接口不属于当前功能')
    backend = current_backend(context)
    if backend is None:
        raise RuntimeError('请先执行“绑定选择窗口”指令')
    backend.failSafeCheck()
    if group in ('后台图色操作', '后台文字识别'):
        backend.require_capture()
    if hasattr(backend.transport, 'capabilities') and name not in backend.transport.capabilities:
        raise ValueError(f'当前组件未提供 {name} 接口，请在组件设置中选择支持此接口的版本')
    values = json.loads(parameters.get('参数', '{}'))
    if not isinstance(values, dict):
        raise ValueError('后台参数必须为对象')
    values = {key: substitute_variables(context, value) if isinstance(value, str) else value
              for key, value in values.items()}
    arguments = values_for(name, values)
    arguments = [backend.hwnd if value == '@窗口' else value for value in arguments]
    arguments = values_for(name, {item['name']: value for item, value in zip(definition['args'], arguments)
                                 if not item['out'] or item.get('inout')})
    if any(value == '@窗口' for value in arguments):
        raise ValueError('窗口参数解析失败')
    if name.startswith('Faq') and name in ('FaqSend', 'FaqPost'):
        for item, value in zip(definition['args'], arguments):
            if item['name'] in ('server', 'user', 'pwd') and not value:
                raise ValueError('请配置答题服务地址及账号；建议通过变量引用密码')
    if name.startswith(('Read', 'Write', 'Find')) and definition['group'] == '后台内存操作':
        for item, value in zip(definition['args'], arguments):
            if item['name'] == 'addr' and not value:
                raise ValueError('请填写地址表达式')
    # These calls use the same adapter as normal instructions, including held-input cleanup.
    if name == 'CaptureArray':
        import base64
        x1,y1,x2,y2 = arguments
        image = backend.screenshot(region=(x1,y1,x2-x1,y2-y1))
        result = {'width': image.width, 'height': image.height, 'format': 'RGB',
                  'data_base64': base64.b64encode(image.tobytes()).decode('ascii')}
    elif name in ('KeyDownChar','KeyUpChar'):
        (backend.keyDown if name == 'KeyDownChar' else backend.keyUp)(arguments[0])
        result = 1
    elif name in ('KeyDown', 'KeyUp'):
        vk = int(arguments[0])
        if not 1 <= vk <= 255:
            raise ValueError('虚拟键码必须在 1–255 之间')
        if name == 'KeyDown':
            backend.keys.add(vk)
        result = backend._call(name, vk)
        if name == 'KeyUp':
            backend.keys.discard(vk)
    elif name in ('LeftDown','LeftUp','RightDown','RightUp','MiddleDown','MiddleUp'):
        button = name[:-4].lower() if name.endswith('Down') else name[:-2].lower()
        (backend.mouseDown if name.endswith('Down') else backend.mouseUp)(button=button)
        result = 1
    elif name in ('MoveTo', 'MoveR'):
        (backend.moveTo if name == 'MoveTo' else backend.moveRel)(*arguments)
        result = 1
    else:
        result = backend.transport.call(name, *arguments, raw=True)
    if name in ['SetExactOcr','SetMinRowGap','SetMinColGap','SetWordLineHeight','SetWordGap','SetRowGapNoDict','SetColGapNoDict','SetWordLineHeightNoDict','SetWordGapNoDict','SetPath','SetDict','UseDict','AddDict','ClearDict','SaveDict','SetDictPwd','SetExportDict','EncodeFile','DecodeFile','Capture','CapturePng','CaptureJpg','CaptureGif','LoadPic','FreePic','SetPicPwd','ImageToBmp','MoveTo','MoveR','LeftClick','RightClick','MiddleClick','LeftDoubleClick','LeftDown','LeftUp','RightDown','RightUp','WheelUp','WheelDown','KeyDown','KeyUp','KeyPress','KeyDownChar','KeyUpChar','KeyPressChar','KeyPressStr','SetMouseDelay','SetKeypadDelay','MiddleDown','MiddleUp','SetWindowText','SetWindowSize','SetClientSize','MoveWindow','SetWindowState','SetWindowTransparent','FoobarFillRect','FoobarDrawText','FoobarDrawPic','FoobarDrawLine','FoobarUpdate','FoobarLock','FoobarUnlock','FoobarSetFont','FoobarTextRect','FoobarPrintText','FoobarClearText','FoobarTextLineGap','FoobarTextPrintDir','FoobarSetSave','FoobarClose','FoobarStartGif','FoobarStopGif','FoobarSetTrans','WriteInt','WriteFloat','WriteDouble','WriteString','WriteData','AsmAdd','AsmClear'] and result != 1:
        raise RuntimeError(f'后台操作 {name} 失败，返回码 {result}')
    variable = str(parameters.get('变量', '')).strip()
    context.set_variable(variable, result)
    context.emit(f'{group}：{definition["label"]} 完成' + (f'，结果已保存至 {variable}' if variable else ''))
    return result
