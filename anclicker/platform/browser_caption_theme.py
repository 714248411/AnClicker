"""Color only the bundled browser process's native Windows captions."""
import sys

def apply_browser_caption_theme(pid,mode):
    if sys.platform!='win32' or mode not in ('light','dark') or not pid:return
    import ctypes
    from ctypes import wintypes
    import win32gui,win32process
    dark=mode=='dark'
    inactive=(24,24,27) if dark else (241,241,243)
    active=(9,9,11) if dark else (247,247,248)
    foreground=(241,241,243) if dark else (47,47,47)
    dwm=ctypes.windll.dwmapi.DwmSetWindowAttribute
    dwm.argtypes=[wintypes.HWND,wintypes.DWORD,ctypes.c_void_p,wintypes.DWORD]
    def attribute(hwnd,key,value):
        number=ctypes.c_int(value)
        return dwm(hwnd,key,ctypes.byref(number),ctypes.sizeof(number))
    def visit(hwnd,_):
        try:
            if win32process.GetWindowThreadProcessId(hwnd)[1]!=pid:return
            if not win32gui.GetClassName(hwnd).startswith('Chrome_WidgetWin'):return
            # Bundled page windows now own a themed caption, including on Win10.
            if win32gui.GetWindowText(hwnd).startswith('极速网页AC'):return
            focused=hwnd==win32gui.GetForegroundWindow()
            background=active if focused else inactive
            attribute(hwnd,20,int(dark))
            caption_result=attribute(hwnd,35,background[0]|background[1]<<8|background[2]<<16)
            attribute(hwnd,36,foreground[0]|foreground[1]<<8|foreground[2]<<16)
            if caption_result < 0:
                # Windows 10 has no custom caption colors. Its dark inactive
                # caption is black, while its active caption is gray. Repaint
                # only the non-client appearance; never change actual focus.
                painted_active=not focused if dark else focused
                win32gui.DefWindowProc(hwnd,0x0086,int(painted_active),0)
        except win32gui.error:pass  # A browser may close during enumeration.
    win32gui.EnumWindows(visit,None)
