"""Desktop platform services; GUI dependencies are loaded on demand."""
import os
import sys
import shutil
import subprocess
import typing

from anclicker._imports import DeferredImports as _DeferredImports

# Dependencies declared here retain their existing on-demand loading boundaries.
_module_imports = _DeferredImports(globals(), {
    'win32con': ('import', 'win32con', (), False),
    'win32gui': ('import', 'win32gui', (), False),
    'SystemHotkey': ('from', 'system_hotkey', ('SystemHotkey',), 0),
    'user32': ('from', 'system_hotkey', ('user32',), 0),
    'QGuiApplication': ('from', 'anclicker.platform.qt_compat.QtGui', ('QGuiApplication',), 0),
    'winsound': ('import', 'winsound', (), False),
    'QApplication': ('from', 'anclicker.platform.qt_compat.QtWidgets', ('QApplication',), 0),
})


try:
    win32con = _module_imports.load('win32con')
    win32gui = _module_imports.load('win32gui')
except ImportError:  # pragma: no cover - exercised on macOS/Linux runners
    win32con = None
    win32gui = None

try:
    SystemHotkey = _module_imports.load('SystemHotkey')
    try:
        user32 = _module_imports.load('user32')
    except ImportError:
        user32 = None
except (ImportError, OSError):  # macOS has no supported system-hotkey backend
    SystemHotkey = None
    user32 = None


class NullSystemHotkey:
    """No-op backend used when global hotkeys are unavailable on the host."""

    supported = False

    def register(self, *args, **kwargs):
        del args, kwargs
        raise RuntimeError("当前系统没有可用的全局快捷键后端")

    def unregister(self, *args, **kwargs):
        del args, kwargs


def create_system_hotkey():
    """Create the native global-hotkey backend without breaking app startup."""
    if SystemHotkey is None or "--startup-smoke-test" in sys.argv:
        return NullSystemHotkey()
    try:
        backend_ = SystemHotkey()
        backend_.supported = True
        return backend_
    except Exception:
        return NullSystemHotkey()


def global_hotkeys_supported(hkobj=None) -> bool:
    return bool(getattr(hkobj, "supported", SystemHotkey is not None))


def is_hotkey_valid(hkobj, hk: typing.List[str]):
    """判断快捷键是否有效"""
    if not global_hotkeys_supported(hkobj):
        return False
    hk = hkobj.order_hotkey(hk)
    try:
        if sys.platform == "win32" and user32 is not None:
            keycode, masks = hkobj.parse_hotkeylist(hk)
            reg_hk_res = user32.RegisterHotKey(None, 1, masks, keycode)
            if reg_hk_res:
                user32.UnregisterHotKey(None, 1)
                return True
        else:
            hkobj.register(hk, callback=lambda *_: None, overwrite=False)
            hkobj.unregister(tuple(hk))
            return True
    except Exception as e:
        print("获取快捷键注册信息失败！", e)
    return False


def show_window(title):
    """将指定标题的窗口正常显示，主要用于主窗口显示"""

    if win32gui is None or win32con is None:
        return False

    def get_window_titles(hwnd, titles):
        titles[hwnd] = win32gui.GetWindowText(hwnd)

    try:
        hwnd_title = {}
        win32gui.EnumWindows(get_window_titles, hwnd_title)
        for h, t in hwnd_title.items():
            if t == title:
                win32gui.ShowWindow(h, win32con.SW_SHOWNORMAL)  # 正常显示窗口
                win32gui.SetForegroundWindow(h)
                return True
    except Exception as e:
        print(f"显示窗口出现错误: {e}")
    return False


def open_path(path_: str) -> None:
    """Open a file or directory with the host desktop's default application."""
    normalized_ = os.path.abspath(os.path.expanduser(path_))
    if sys.platform == "win32":
        os.startfile(normalized_)
    elif sys.platform == "darwin":
        subprocess.Popen(["open", normalized_])
    else:
        opener_ = shutil.which("xdg-open") or shutil.which("gio")
        if opener_ is None:
            raise OSError("未找到 xdg-open 或 gio，无法打开路径")
        command_ = [opener_, normalized_]
        if os.path.basename(opener_) == "gio":
            command_.insert(1, "open")
        subprocess.Popen(command_)


def get_screen_resolution() -> str:
    """Return the primary screen size using Qt on every desktop platform."""
    try:
        QGuiApplication = _module_imports.load('QGuiApplication')

        app_ = QGuiApplication.instance()
        screen_ = app_.primaryScreen() if app_ is not None else None
        if screen_ is not None:
            size_ = screen_.size()
            return f"{size_.width()}*{size_.height()}"
    except Exception:
        pass
    return "1920*1080"


def play_system_tone(frequency_: int = 500, duration_ms_: int = 300) -> None:
    """Play a notification tone with a Windows-native and Qt fallback path."""
    if sys.platform == "win32":
        try:
            winsound = _module_imports.load('winsound')

            winsound.Beep(frequency_, duration_ms_)
            return
        except (ImportError, RuntimeError):
            pass
    try:
        QApplication = _module_imports.load('QApplication')

        QApplication.beep()
    except Exception:
        pass
