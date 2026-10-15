"""Windows display initialization without importing Qt or input libraries."""
import ctypes
import sys


def configure_dpi(user32=None, shcore=None):
    """Choose per-monitor DPI before libraries can select system-DPI mode.

    Windows 10 1607 understands PerMonitor (-3); 1703+ also understands V2
    (-4). Resolve APIs dynamically and retain the older-system fallback.
    An existing manifest/host policy (access denied) must not be overwritten.
    """
    if sys.platform != 'win32' and user32 is None:
        return 'not-windows'
    user32 = user32 or ctypes.WinDLL('user32', use_last_error=True)
    setter = getattr(user32, 'SetProcessDpiAwarenessContext', None)
    if setter is not None:
        setter.argtypes = [ctypes.c_void_p]
        setter.restype = ctypes.c_int
        for context, label in ((-4, 'per-monitor-v2'), (-3, 'per-monitor')):
            ctypes.set_last_error(0)
            if setter(context):
                return label
            if ctypes.get_last_error() == 5:
                return 'existing-policy'
    try:
        shcore = shcore or ctypes.WinDLL('shcore', use_last_error=True)
        setter = shcore.SetProcessDpiAwareness
        setter.argtypes = [ctypes.c_int]
        setter.restype = ctypes.c_long
        result = setter(2)
        if result == 0:
            return 'per-monitor'
        if result & 0xffffffff == 0x80070005:
            return 'existing-policy'
    except (OSError, AttributeError):
        pass
    return 'system' if user32.SetProcessDPIAware() else 'existing-policy'
