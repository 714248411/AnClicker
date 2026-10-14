"""Keep one Qt application alive and finish deferred deletion before teardown."""
import pytest
from qt_compat.QtCore import QCoreApplication, QEvent
from qt_compat.QtWidgets import QApplication


@pytest.fixture(scope='session', autouse=True)
def qt_application():
    application = QApplication.instance() or QApplication([])
    yield application
    QCoreApplication.sendPostedEvents(None, QEvent.DeferredDelete)
    application.processEvents()
