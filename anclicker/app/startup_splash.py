from anclicker.app.paths import resource_path
"""Lightweight animated startup card; readiness never waits for a movie loop."""
from anclicker.platform.qt_compat.QtCore import Qt, QSize, QRectF
from anclicker.platform.qt_compat.QtGui import QColor, QFont, QMovie, QPainter, QPainterPath, QPixmap
from anclicker.platform.qt_compat.QtWidgets import QSplashScreen

from anclicker._imports import DeferredImports as _DeferredImports

# Dependencies declared here retain their existing on-demand loading boundaries.
_module_imports = _DeferredImports(globals(), {
    'Path': ('from', 'pathlib', ('Path',), 0),
    'threading': ('import', 'threading', (), False),
    'subprocess': ('import', 'subprocess', (), False),
    'sys': ('import', 'sys', (), False),
    'configure_application': ('from', 'anclicker.platform.qt_compat', ('configure_application',), 0),
    'QTimer': ('from', 'anclicker.platform.qt_compat.QtCore', ('QTimer',), 0),
    'QApplication': ('from', 'anclicker.platform.qt_compat.QtWidgets', ('QApplication',), 0),
    'ctypes': ('import', 'ctypes', (), False),
    'msvcrt': ('import', 'msvcrt', (), False),
    'os': ('import', 'os', (), False),
})



class LoadingSplashScreen(QSplashScreen):
    def __init__(self, image_path, side=540):
        super().__init__()
        self._finished = False
        self._side = side
        self.setAttribute(Qt.WA_TranslucentBackground, True)
        canvas = QPixmap(side + 24, side + 76)
        canvas.fill(Qt.transparent)
        self.movie = QMovie(str(image_path), parent=self)
        # Decode only the current frame, rather than caching the entire GIF.
        self.movie.setCacheMode(QMovie.CacheNone)
        self.movie.setScaledSize(QSize(side, side))
        self.movie.frameChanged.connect(self._frame_changed)
        Path = _module_imports.load('Path')
        self._fallback = QPixmap(str(Path(image_path).with_name('startup-fallback.png'))).scaled(
            side, side, Qt.KeepAspectRatio, Qt.SmoothTransformation)
        self._static_mode = False
        self.movie.error.connect(self._use_fallback)
        self._card_path = QPainterPath()
        self._card_path.addRoundedRect(QRectF(12, 8, side, side + 52), 20, 20)
        painter = QPainter(canvas)
        self._draw_shell(painter)
        painter.end()
        self.setPixmap(canvas)
        if self.movie.isValid():
            self.movie.start()
        else:
            self._use_fallback()

    def _frame_changed(self, _frame):
        if not self._finished:
            self.update(12, 8, self._side, self._side)

    def _use_fallback(self, *_args):
        self.movie.stop()
        self._static_mode = True
        self.update()

    def _draw_shell(self, painter):
        # Render the fixed glass shell once, not on every animation frame.
        painter.setRenderHint(QPainter.Antialiasing)
        card = QRectF(12, 8, self._side, self._side + 52)
        for spread in range(8, 0, -1):
            painter.setPen(Qt.NoPen)
            painter.setBrush(QColor(30, 35, 50, 2))
            painter.drawRoundedRect(card.adjusted(-spread, -spread / 2, spread, spread), 22, 22)
        painter.setPen(QColor(255, 255, 255, 235))
        painter.setBrush(QColor(255, 255, 255, 238))
        painter.drawRoundedRect(card, 20, 20)
        painter.setPen(QColor('#737d8d'))
        painter.setFont(QFont('Microsoft YaHei', 10))
        painter.drawText(QRectF(24, self._side + 14, self._side - 24, 34),
                         Qt.AlignCenter, '正在加载，完成后自动进入主页…')

    def drawContents(self, painter):
        painter.save()
        painter.setRenderHint(QPainter.Antialiasing)
        painter.setClipPath(self._card_path)
        frame = self._fallback if self._static_mode else self.movie.currentPixmap()
        if frame.isNull():
            frame = self._fallback
        if not frame.isNull():
            target = QRectF(12, 8, self._side, self._side)
            scaled = frame.size().scaled(QSize(self._side, self._side), Qt.KeepAspectRatio)
            target.setSize(scaled)
            target.moveCenter(QRectF(12, 8, self._side, self._side).center())
            painter.drawPixmap(target, frame, QRectF(frame.rect()))
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
        threading = _module_imports.load('threading')
        def reap():
            subprocess = _module_imports.load('subprocess')
            try:
                self.process.wait(timeout=2)
            except subprocess.TimeoutExpired:
                self.process.terminate()
                self.process.wait()
        threading.Thread(target=reap, daemon=True).start()

    def deleteLater(self):
        pass


def show_splash_screen(app, image_path):
    subprocess = _module_imports.load('subprocess')
    sys = _module_imports.load('sys')
    Path = _module_imports.load('Path')
    command = ([sys.executable] if getattr(sys, 'frozen', False) else
               [sys.executable, str(resource_path('main.py'))])
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
    sys = _module_imports.load('sys')
    threading = _module_imports.load('threading')
    configure_application = _module_imports.load('configure_application')
    QTimer = _module_imports.load('QTimer')
    QApplication = _module_imports.load('QApplication')
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
                ctypes = _module_imports.load('ctypes')
                msvcrt = _module_imports.load('msvcrt')
                os = _module_imports.load('os')
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
