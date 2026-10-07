"""Qt5-only adapter for An Clicker's legacy Windows distribution.

QtPy normalizes binding names; this package pins the backend so PySide/Qt6
cannot be imported into the same process accidentally.
"""
import os
import sys
os.environ['QT_API'] = 'pyqt5'
from qtpy import QtCore, QtGui, QtWidgets, QtTest, QtNetwork, QtPrintSupport
for module in (QtCore, QtGui, QtWidgets, QtTest, QtNetwork, QtPrintSupport):
    sys.modules[__name__ + '.' + module.__name__.rsplit('.', 1)[-1]] = module

from PyQt5 import sip
def isValid(obj):
    return obj is not None and not sip.isdeleted(obj)

def _set_row_visible(layout, row, visible):
    if not isinstance(row, int):
        row = layout.getWidgetPosition(row)[0]
    for role in (QtWidgets.QFormLayout.LabelRole, QtWidgets.QFormLayout.FieldRole):
        item = layout.itemAt(row, role)
        if item is not None:
            _show_layout_item(item, visible)

def _show_layout_item(item, visible):
    if item.widget() is not None:
        item.widget().setVisible(visible)
    elif item.layout() is not None:
        child = item.layout()
        for index in range(child.count()):
            _show_layout_item(child.itemAt(index), visible)

if not hasattr(QtWidgets.QFormLayout, 'setRowVisible'):
    QtWidgets.QFormLayout.setRowVisible = _set_row_visible

# QSignalSpy is list-like in PyQt, while the existing regression suite uses at().
if not hasattr(QtTest.QSignalSpy, 'at'):
    QtTest.QSignalSpy.at = lambda self, index: self[index]
