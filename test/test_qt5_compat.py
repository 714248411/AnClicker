import sys
import os
import pytest
os.environ.setdefault('QT_QPA_PLATFORM', 'offscreen')
from qt_compat import QtCore, QtGui, QtWidgets, QtTest, isValid

@pytest.fixture
def qapp():
    app = QtWidgets.QApplication.instance() or QtWidgets.QApplication([])
    yield app
    app.processEvents()

def test_backend_and_signals(qapp):
    from qtpy import API_NAME
    assert API_NAME == 'PyQt5'
    assert QtCore.qVersion() == '5.15.2'
    assert not any(name.startswith(('PySide6', 'PyQt6')) for name in sys.modules)
    button = QtWidgets.QPushButton()
    spy = QtTest.QSignalSpy(button.clicked)
    button.click()
    assert spy.at(0) == [False]
    assert isValid(button)

def test_form_row_visibility(qapp):
    parent = QtWidgets.QWidget()
    form = QtWidgets.QFormLayout(parent)
    field = QtWidgets.QLineEdit()
    form.addRow('value', field)
    form.setRowVisible(0, False)
    assert field.isHidden()
    assert form.labelForField(field).isHidden()
    form.setRowVisible(0, True)
    assert not field.isHidden()
    assert not form.labelForField(field).isHidden()

def test_splash_uses_qrectf(qapp):
    from main import show_splash_screen
    from functions import RESOURCE_FOLDER
    from pathlib import Path
    splash = show_splash_screen(qapp, str(Path(RESOURCE_FOLDER)/'flat/开屏.png'))
    assert not splash.pixmap().isNull()
    splash.close()
