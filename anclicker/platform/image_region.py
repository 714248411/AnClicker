"""Resolve a selected window into the active image backend's coordinates."""
from anclicker.platform.background_runtime import Windows, current_backend


def window_region(target, windows=None, backend=None):
    windows = windows or Windows()
    offsets = target.get('区域偏移')
    crop = target.get('区域比例')
    target = windows.resolve(target)
    windows.validate(target)
    hwnd = int(target['窗口句柄'])
    if windows.gui.IsIconic(hwnd) or not windows.gui.IsWindowVisible(hwnd):
        raise ValueError('区域窗口不可见或已最小化，请先恢复窗口')
    left, top, right, bottom = windows.gui.GetWindowRect(hwnd)
    if right <= left or bottom <= top:
        raise ValueError('区域窗口没有有效范围')
    backend = current_backend() if backend is None else backend
    if crop is not None:
        import math
        values = [float(v) for v in crop]
        if len(values) != 4 or not all(math.isfinite(v) for v in values):
            raise ValueError('窗口区域比例无效，请重新选择范围')
        x,y,w,h=values
        if x < 0 or y < 0 or w <= 0 or h <= 0 or x+w > 1.000001 or y+h > 1.000001:
            raise ValueError('窗口区域比例超出窗口范围')
        width,height=right-left,bottom-top
        left,top=left+round(x*width),top+round(y*height)
        right,bottom=left+max(1,round(w*width)),top+max(1,round(h*height))
    if offsets is not None:
        if len(offsets) != 4: raise ValueError('窗口区域偏移必须包含四个数值')
        dx1,dy1,dx2,dy2 = [int(v) for v in offsets]
        left,top,right,bottom=left+dx1,top+dy1,right+dx2,bottom+dy2
        if right<=left or bottom<=top: raise ValueError('偏移后的区域宽度和高度必须大于 0')
    rectangle = (left, top, right-left, bottom-top)
    return region_in_bound_window(rectangle, backend.target, windows) if backend is not None else rectangle


def region_in_bound_window(rectangle, target, windows=None):
    windows = windows or Windows()
    bound = windows.resolve(target)
    windows.validate(bound)
    origin = windows.gui.ClientToScreen(int(bound['窗口句柄']), (0, 0))
    size = windows.size(bound)
    x, y, width, height = rectangle
    left, top = max(0, x-origin[0]), max(0, y-origin[1])
    right, bottom = min(size.width, x+width-origin[0]), min(size.height, y+height-origin[1])
    if right <= left or bottom <= top:
        raise ValueError('所选区域与当前后台绑定窗口不相交')
    return left, top, right-left, bottom-top
