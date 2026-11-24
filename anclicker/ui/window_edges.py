"""Use desktop-composited rounded edges/shadows without changing client layout."""
import sys
from anclicker.platform.qt_compat.QtCore import QObject,QEvent,QTimer,Qt
from anclicker.platform.qt_compat.QtWidgets import QApplication,QDialog,QMainWindow,QDockWidget,QFileDialog

def uses_native_file_dialog(window):
    # QFileDialog's QWidget is only a proxy for the Windows picker. Creating
    # grips or calling winId() on it materializes an extra empty native window.
    return isinstance(window, QFileDialog) and not window.testOption(QFileDialog.DontUseNativeDialog)

def apply_window_edges(window, owner=None):
    if sys.platform!='win32':return
    if uses_native_file_dialog(window):
        shadow = getattr(window, '_outer_shadow', None)
        if shadow is not None:shadow.hide()
        for grip in getattr(window, '_corner_grips', []):grip.hide()
        return
    for grip in getattr(window,'_corner_grips',[]):grip.sync()
    if not window.isWindow():
        shadow=getattr(window,'_outer_shadow',None)
        if shadow is not None:shadow.hide()
        return
    if window.windowType() in (Qt.Popup,Qt.ToolTip):return
    if window.windowType()==Qt.Tool and not isinstance(window,QDockWidget):return
    from anclicker.ui.context_menu_style import menu_workspace
    workspace=menu_workspace(owner or window)
    if workspace is None:workspace=getattr(window,'_edge_workspace',None)
    elif owner is not None:window._edge_workspace=workspace
    dark=getattr(workspace,'theme_mode','light')=='dark'
    from anclicker.ui.window_shadow import WindowShadow
    shadow=getattr(window,'_outer_shadow',None)
    if shadow is None and window.isVisible() and not window.isMaximized() and not window.isFullScreen():
        shadow=window._outer_shadow=WindowShadow(window)
    if shadow is not None:shadow.sync(dark)
    if not window.isVisible() or window.isFullScreen():return
    from anclicker.ui.window_resize import register_corner_resize
    register_corner_resize(window)
    handle=int(window.winId());signature=(handle,dark,window.isMaximized())
    if getattr(window,'_edge_signature',None)==signature:return
    import ctypes
    from ctypes import wintypes
    class Margins(ctypes.Structure):
        _fields_=[('left',ctypes.c_int),('right',ctypes.c_int),('top',ctypes.c_int),('bottom',ctypes.c_int)]
    dwm=ctypes.windll.dwmapi
    dwm.DwmSetWindowAttribute.argtypes=[wintypes.HWND,wintypes.DWORD,ctypes.c_void_p,wintypes.DWORD]
    dwm.DwmExtendFrameIntoClientArea.argtypes=[wintypes.HWND,ctypes.POINTER(Margins)]
    def attribute(key,value):
        number=ctypes.c_int(value);return dwm.DwmSetWindowAttribute(handle,key,ctypes.byref(number),ctypes.sizeof(number))
    attribute(2,2) # Enable native non-client rendering / composited shadow.
    attribute(20,int(dark))
    attribute(33,1 if window.isMaximized() else 2) # Rounded on Windows 11; ignored on older Windows.
    rgb=(73,76,86) if dark else (218,223,231)
    translucent=window.testAttribute(Qt.WA_TranslucentBackground)
    attribute(34,-2 if translucent else rgb[0]|rgb[1]<<8|rgb[2]<<16)
    margin=0 if window.isMaximized() or translucent else 1
    dwm.DwmExtendFrameIntoClientArea(handle,ctypes.byref(Margins(margin,margin,margin,margin)))
    window._edge_signature=signature

class WindowEdges(QObject):
    def __init__(self,app):
        super().__init__(app);app.installEventFilter(self)
    def eventFilter(self,obj,event):
        if uses_native_file_dialog(obj):
            return False
        if event.type() == QEvent.Hide:
            # Native file dialogs can hide and then block the event loop during
            # import. Remove their separate shadow before any deferred work.
            shadow = getattr(obj, '_outer_shadow', None)
            if shadow is not None:
                shadow.hide()
        if isinstance(obj,(QDialog,QMainWindow,QDockWidget)) and event.type() in (QEvent.Show,QEvent.Hide,QEvent.Move,QEvent.Resize,QEvent.PaletteChange,QEvent.StyleChange,QEvent.WindowStateChange,QEvent.WinIdChange):
            if not hasattr(obj,'_edge_timer'):
                obj._edge_timer=QTimer(obj);obj._edge_timer.setSingleShot(True)
                obj._edge_timer.timeout.connect(lambda:apply_window_edges(obj))
            obj._edge_timer.start(0)
        return False

def install_window_edges():
    app=QApplication.instance()
    if app is not None and not hasattr(app,'_window_edges'):app._window_edges=WindowEdges(app)
