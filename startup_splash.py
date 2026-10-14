"""Lightweight animated startup card; readiness never waits for a movie loop."""
from qt_compat.QtCore import Qt, QSize, QRectF
from qt_compat.QtGui import QColor, QFont, QMovie, QPainter, QPainterPath, QPixmap
from qt_compat.QtWidgets import QSplashScreen


class LoadingSplashScreen(QSplashScreen):
    def __init__(self, image_path, side=540):
        super().__init__()
        self._finished = False
        self._side = side
        self.setAttribute(Qt.WA_TranslucentBackground, True)
        canvas = QPixmap(side + 24, side + 76)
        canvas.fill(Qt.transparent)
        self.setPixmap(canvas)
        self.movie = QMovie(str(image_path), parent=self)
        # Decode only the current frame, rather than caching the entire GIF.
        self.movie.setCacheMode(QMovie.CacheNone)
        self.movie.setScaledSize(QSize(side, side))
        self.movie.frameChanged.connect(self._frame_changed)
        self.movie.start()

    def _frame_changed(self, _frame):
        if not self._finished:
            self.update()

    def drawContents(self, painter):
        painter.save()
        painter.setRenderHint(QPainter.Antialiasing)
        card = QRectF(12, 8, self._side, self._side + 52)
        # A soft translucent white shell stays readable in both app themes.
        for spread in range(8, 0, -1):
            painter.setPen(Qt.NoPen)
            painter.setBrush(QColor(30, 35, 50, 2))
            painter.drawRoundedRect(card.adjusted(-spread, -spread / 2, spread, spread), 22, 22)
        painter.setPen(QColor(255, 255, 255, 235))
        painter.setBrush(QColor(255, 255, 255, 238))
        painter.drawRoundedRect(card, 20, 20)
        path = QPainterPath()
        path.addRoundedRect(card, 20, 20)
        painter.setClipPath(path)
        frame = self.movie.currentPixmap()
        if not frame.isNull():
            target = QRectF(12, 8, self._side, self._side)
            scaled = frame.size().scaled(QSize(self._side, self._side), Qt.KeepAspectRatio)
            target.setSize(scaled)
            target.moveCenter(QRectF(12, 8, self._side, self._side).center())
            painter.drawPixmap(target, frame, QRectF(frame.rect()))
        painter.setPen(QColor('#737d8d'))
        painter.setFont(QFont('Microsoft YaHei', 10))
        painter.drawText(QRectF(24, self._side + 14, self._side - 24, 34),
                         Qt.AlignCenter, '正在加载，完成后自动进入主页…')
        painter.restore()

    def finish(self, main_window):
        # No artificial minimum display time, animation-end signal or fade-out.
        self._finished = True
        self.movie.stop()
        self.hide()
        self.close()

    def closeEvent(self, event):
        self._finished = True
        self.movie.stop()
        super().closeEvent(event)


def show_local_splash(app, image_path):
    screen = app.primaryScreen()
    side = 540
    if screen is not None:
        bounds = screen.availableGeometry()
        side = max(180, min(side, bounds.width() - 48, bounds.height() - 112))
    splash = LoadingSplashScreen(image_path, side)
    if screen is not None:
        splash.move(bounds.center() - splash.rect().center())
    splash.show()
    app.processEvents()
    return splash


class SplashProcess:
    """Keep GIF playback responsive while the main GUI imports and initializes."""
    def __init__(self, process):
        self.process = process

    def finish(self, main_window=None):
        if self.process.stdin is not None:
            try:
                self.process.stdin.close()
            except OSError:
                pass
            self.process.stdin = None
        # Reap asynchronously: never delay the ready main window.
        import threading
        def reap():
            import subprocess
            try:
                self.process.wait(timeout=2)
            except subprocess.TimeoutExpired:
                self.process.terminate()
                self.process.wait()
        threading.Thread(target=reap, daemon=True).start()

    def deleteLater(self):
        pass


def show_splash_screen(app, image_path):
    import subprocess
    import sys
    from pathlib import Path
    command = ([sys.executable] if getattr(sys, 'frozen', False) else
               [sys.executable, str(Path(__file__).with_name('main.py'))])
    try:
        process = subprocess.Popen(command + ['--startup-animation', str(image_path)],
                                   stdin=subprocess.PIPE, stdout=subprocess.DEVNULL,
                                   stderr=subprocess.DEVNULL,
                                   creationflags=getattr(subprocess, 'CREATE_NO_WINDOW', 0))
    except OSError:
        return show_local_splash(app, image_path)
    splash = SplashProcess(process)
    app.aboutToQuit.connect(splash.finish)
    return splash


def run_animation(image_path):
    import sys
    import threading
    from qt_compat import configure_application
    from qt_compat.QtCore import QTimer
    from qt_compat.QtWidgets import QApplication
    configure_application()
    app = QApplication([sys.argv[0]])
    done = threading.Event()
    def watch_parent():
        # EOF also arrives if the parent crashes, so no orphan splash remains.
        try:
            if sys.stdin is not None:
                sys.stdin.buffer.read()
            elif sys.platform == 'win32':
                # PyInstaller windowed executables intentionally set stdin=None.
                import ctypes
                import msvcrt
                import os
                kernel = ctypes.WinDLL('kernel32', use_last_error=True)
                kernel.GetStdHandle.argtypes = [ctypes.c_uint32]
                kernel.GetStdHandle.restype = ctypes.c_void_p
                handle = kernel.GetStdHandle(ctypes.c_uint32(-10))
                descriptor = msvcrt.open_osfhandle(handle, os.O_RDONLY)
                with os.fdopen(descriptor, 'rb') as stream:
                    stream.read()
        finally:
            done.set()
    threading.Thread(target=watch_parent, daemon=True).start()
    # A very fast startup may finish before this process creates its window.
    if done.is_set():
        return 0
    splash = show_local_splash(app, image_path)
    timer = QTimer(app)
    def check_ready():
        if done.is_set():
            splash.finish(None)
            app.quit()
    timer.timeout.connect(check_ready)
    timer.start(16)
    return app.exec()
