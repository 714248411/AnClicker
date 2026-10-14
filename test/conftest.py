"""Keep one Qt application alive and finish deferred deletion before teardown."""
import pytest
from qt_compat.QtCore import QCoreApplication, QEvent
from qt_compat.QtWidgets import QApplication


# Pytest performs a final garbage collection after session fixtures are torn down.
# Keep Qt alive through that phase so surviving widget wrappers can be collected.
_application = None


@pytest.fixture(scope='session', autouse=True)
def qt_application():
    global _application
    application = _application = QApplication.instance() or QApplication([])
    yield application
    QCoreApplication.sendPostedEvents(None, QEvent.DeferredDelete)
    application.processEvents()
