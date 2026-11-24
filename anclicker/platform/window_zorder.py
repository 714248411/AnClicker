"""Set and verify native Windows Z order, including inactive/minimized windows."""
import sys
import time
from anclicker._imports import DeferredImports

_imports = DeferredImports(globals(), {
    'win32gui': ('import', 'win32gui', (), False),
    'win32con': ('import', 'win32con', (), False),
})


def set_window_zorder(hwnd, operation):
    if sys.platform != 'win32':raise RuntimeError('此窗口层级接口仅用于 Windows')
    gui, constants = _imports.load('win32gui'), _imports.load('win32con')
    if operation not in ('置顶','置底'):raise ValueError('未知窗口层级操作')
    hwnd=int(hwnd)
    if not gui.IsWindow(hwnd):raise RuntimeError('目标窗口已关闭，请重新点选窗口')
    hwnd=gui.GetAncestor(hwnd,2) or hwnd
    flags=constants.SWP_NOMOVE | constants.SWP_NOSIZE | constants.SWP_NOACTIVATE
    if operation=='置底':
        gui.SetWindowPos(hwnd,constants.HWND_BOTTOM,0,0,0,0,flags)
        if gui.GetWindowLong(hwnd,constants.GWL_EXSTYLE)&constants.WS_EX_TOPMOST:
            raise RuntimeError('目标窗口拒绝取消置顶，请检查目标程序的置顶设置和权限')
        return
    if gui.IsIconic(hwnd):gui.ShowWindow(hwnd,constants.SW_RESTORE)
    elif not gui.IsWindowVisible(hwnd):gui.ShowWindow(hwnd,constants.SW_SHOWNOACTIVATE)
    gui.SetWindowPos(hwnd,constants.HWND_TOPMOST,0,0,0,0,flags)
    if not gui.GetWindowLong(hwnd,constants.GWL_EXSTYLE)&constants.WS_EX_TOPMOST:
        # Some inactive native windows ignore the first Z-order change. A
        # foreground transition is needed before setting their persistent level.
        try:gui.SetForegroundWindow(hwnd)
        except gui.error:pass
        gui.SetWindowPos(hwnd,constants.HWND_NOTOPMOST,0,0,0,0,flags)
        gui.SetWindowPos(hwnd,constants.HWND_TOPMOST,0,0,0,0,flags|constants.SWP_SHOWWINDOW)
    for _ in range(10):
        if gui.GetWindowLong(hwnd,constants.GWL_EXSTYLE)&constants.WS_EX_TOPMOST:return
        time.sleep(.02)
    raise RuntimeError('置顶未生效：目标程序可能限制窗口层级，或需要以相同权限运行 AnClicker；请先激活目标窗口后重试')
