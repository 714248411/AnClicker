"""A Windows file-picker proxy must not acquire another native window or shadow."""
import sys
from pathlib import Path
from unittest.mock import patch
sys.path.insert(0, str(Path(__file__).resolve().parents[1]))
from anclicker.platform.qt_compat.QtCore import QEvent
from anclicker.platform.qt_compat.QtWidgets import QApplication, QFileDialog
from anclicker.ui.window_edges import apply_window_edges, install_window_edges, uses_native_file_dialog

app = QApplication.instance() or QApplication([])
install_window_edges()
dialog = QFileDialog()
with patch.object(dialog, 'winId', side_effect=AssertionError('native proxy materialized')):
    for kind in (QEvent.Show, QEvent.Resize, QEvent.WinIdChange, QEvent.Hide):
        app._window_edges.eventFilter(dialog, QEvent(kind))
        apply_window_edges(dialog)
assert not hasattr(dialog, '_edge_timer')
assert not hasattr(dialog, '_outer_shadow')
assert not hasattr(dialog, '_corner_grips')
if '--native' in sys.argv:
    # Exercise the actual Windows picker and its nested event loop, without
    # choosing a file or touching the user's running application.
    import ctypes
    from ctypes import wintypes
    import os
    import threading
    import time
    dialog.setWindowTitle('AnClicker native picker regression')
    closed = threading.Event()
    def dismiss_probe():
        # Windows native modal dialogs do not dispatch Qt timers. Close only
        # this test process's named picker through its native message queue.
        user = ctypes.windll.user32
        callback_type = ctypes.WINFUNCTYPE(wintypes.BOOL, wintypes.HWND, wintypes.LPARAM)
        user.GetWindowThreadProcessId.argtypes = [wintypes.HWND, ctypes.POINTER(wintypes.DWORD)]
        user.GetWindowTextW.argtypes = [wintypes.HWND, wintypes.LPWSTR, ctypes.c_int]
        user.PostMessageW.argtypes = [wintypes.HWND, wintypes.UINT, wintypes.WPARAM, wintypes.LPARAM]
        @callback_type
        def visit(hwnd, _):
            pid = wintypes.DWORD()
            user.GetWindowThreadProcessId(hwnd, ctypes.byref(pid))
            title = ctypes.create_unicode_buffer(256)
            user.GetWindowTextW(hwnd, title, len(title))
            if pid.value == os.getpid() and title.value == 'AnClicker native picker regression':
                user.PostMessageW(hwnd, 0x0010, 0, 0)
                closed.set()
            return True
        for _ in range(100):
            time.sleep(.1)
            user.EnumWindows(visit, 0)
            if closed.is_set():return
    worker = threading.Thread(target=dismiss_probe, daemon=True)
    worker.start()
    dialog.exec()
    worker.join(2)
    assert closed.is_set()
    assert not hasattr(dialog, '_outer_shadow')
    assert not hasattr(dialog, '_corner_grips')
    app.processEvents()
    assert not any(widget.isVisible() for widget in app.topLevelWidgets())
custom = QFileDialog()
custom.setOption(QFileDialog.DontUseNativeDialog, True)
assert not uses_native_file_dialog(custom)
custom.deleteLater()
dialog.deleteLater()
print('PASS native file dialog bypasses shadow, grips, winId and deferred styling')
