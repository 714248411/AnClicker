import os
os.environ.setdefault('QT_QPA_PLATFORM', 'offscreen')
from qt_compat.QtCore import QObject, QPoint, QSignalBlocker, QTimer
from qt_compat.QtWidgets import QApplication, QMenu


def test_nested_signal_blockers_restore_previous_state_after_exception():
    obj = QObject()
    try:
        with QSignalBlocker(obj):
            with QSignalBlocker(obj):
                assert obj.signalsBlocked()
            assert obj.signalsBlocked()
            raise ValueError('leave scope')
    except ValueError:
        pass
    assert not obj.signalsBlocked()
    obj.blockSignals(True)
    with QSignalBlocker(obj):
        pass
    assert obj.signalsBlocked()


def test_menu_exec_keeps_instance_binding():
    app = QApplication.instance() or QApplication([])
    menu = QMenu()
    menu.addAction('Close')
    QTimer.singleShot(30, menu.close)
    assert menu.exec(QPoint(0, 0)) is None
    menu.deleteLater()
    app.processEvents()
