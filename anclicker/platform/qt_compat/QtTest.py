"""Qt test helpers, loaded only by tests."""
from . import BINDING

from anclicker._imports import DeferredImports as _DeferredImports

# Dependencies declared here retain their existing on-demand loading boundaries.
_module_imports = _DeferredImports(globals(), {
    'time': ('import', 'time', (), False),
    'QTest': ('from', 'PySide2.QtTest', ('QTest',), 0),
    'QCoreApplication_QElapsedTimer_QEventLoop': ('from', 'PySide2.QtCore', ('QCoreApplication', 'QElapsedTimer', 'QEventLoop'), 0),
    'QTest_2': ('from', 'PySide6.QtTest', ('QTest',), 0),
})


if BINDING == 'PySide2':
    time = _module_imports.load('time')
    QTest = _module_imports.load('QTest')
    QCoreApplication, QElapsedTimer, QEventLoop = _module_imports.load('QCoreApplication_QElapsedTimer_QEventLoop')

    def _qwait(milliseconds):
        timer = QElapsedTimer()
        timer.start()
        while timer.elapsed() < milliseconds:
            QCoreApplication.processEvents(QEventLoop.AllEvents, 10)
            time.sleep(0.001)

    QTest.qWait = staticmethod(_qwait)
else:
    QTest = _module_imports.load('QTest_2')
