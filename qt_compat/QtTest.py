"""Qt test helpers, loaded only by tests."""
from . import BINDING

if BINDING == 'PySide2':
    import time
    from PySide2.QtTest import QTest
    from PySide2.QtCore import QCoreApplication, QElapsedTimer, QEventLoop

    def _qwait(milliseconds):
        timer = QElapsedTimer()
        timer.start()
        while timer.elapsed() < milliseconds:
            QCoreApplication.processEvents(QEventLoop.AllEvents, 10)
            time.sleep(0.001)

    QTest.qWait = staticmethod(_qwait)
else:
    from PySide6.QtTest import QTest
