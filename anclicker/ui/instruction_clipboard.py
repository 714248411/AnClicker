"""Keep Qt clipboard ownership stable across Python/Qt event cycles."""
from anclicker.platform.qt_compat.QtWidgets import QApplication

COMMAND_MIME = 'application/x-anclicker-commands'


def clipboard():
    app = QApplication.instance()
    if not hasattr(app, '_instruction_clipboard'):
        app._instruction_clipboard = QApplication.clipboard()
    return app._instruction_clipboard


def set_command_mime(mime):
    from anclicker.platform.qt_compat.QtCore import QMimeData, QThread
    target = clipboard()
    payload = {kind: bytes(mime.data(kind)) for kind in mime.formats()}
    expected = payload.get(COMMAND_MIME)
    if QApplication.platformName() == "windows":
        import win32clipboard
        import win32con
        for attempt in range(5):
            try:
                win32clipboard.OpenClipboard(int(QApplication.activeWindow().winId()) if QApplication.activeWindow() else 0)
                try:
                    win32clipboard.EmptyClipboard()
                    win32clipboard.SetClipboardData(win32clipboard.RegisterClipboardFormat(COMMAND_MIME), expected)
                    win32clipboard.SetClipboardData(win32con.CF_UNICODETEXT, mime.text())
                finally:
                    win32clipboard.CloseClipboard()
                return
            except Exception:
                QThread.msleep(20)
        raise RuntimeError("剪贴板正被占用，请稍后重试；原指令未剪切。")
    for attempt in range(5):
        current = QMimeData()
        for kind, data in payload.items():
            current.setData(kind, data)
        target.setMimeData(current)
        target._command_mime_owner = current
        if command_clipboard_data() == expected:
            return
        QThread.msleep(20)
    # A failed copy must never be followed by deleting the source commands.
    raise RuntimeError('剪贴板正被占用，请稍后重试；原指令未剪切。')


def command_clipboard_data():
    if QApplication.platformName() == "windows":
        import win32clipboard
        from anclicker.platform.qt_compat.QtCore import QThread
        for attempt in range(5):
            try:
                win32clipboard.OpenClipboard()
                try:
                    kind = win32clipboard.RegisterClipboardFormat(COMMAND_MIME)
                    return bytes(win32clipboard.GetClipboardData(kind)) if win32clipboard.IsClipboardFormatAvailable(kind) else None
                finally:
                    win32clipboard.CloseClipboard()
            except Exception:
                QThread.msleep(20)
        return None
    for _ in range(2):
        try:
            mime = clipboard().mimeData()
            return bytes(mime.data(COMMAND_MIME)) if mime is not None and mime.hasFormat(COMMAND_MIME) else None
        except RuntimeError:
            # The system clipboard may be replaced while its contents are read.
            continue
    return None
