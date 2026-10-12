"""One application API; Windows uses Qt 5.15 for its Windows 10 1607 baseline.

The binding is selected once per process. Never fall back to Qt 6 on Windows:
that would silently reintroduce its newer operating-system requirement.
"""
import sys

if sys.platform == 'win32':
    from PySide2 import QtCore, QtGui, QtWidgets
    BINDING = 'PySide2'
else:
    from PySide6 import QtCore, QtGui, QtWidgets
    BINDING = 'PySide6'

if BINDING == 'PySide2':
    class SignalBlocker:
        """Context-manager support for the application's scoped signal blocks."""
        def __init__(self, obj):
            self._object = obj
            self._previous = obj.blockSignals(True)
            self._active = True

        def __enter__(self):
            return self

        def __exit__(self, *_):
            self.unblock()

        def unblock(self):
            if self._active:
                self._object.blockSignals(self._previous)
                self._active = False

        def reblock(self):
            self._object.blockSignals(True)
            self._active = True

    QtCore.QSignalBlocker = SignalBlocker

    def _set_row_visible(self, row, visible):
        if not isinstance(row, int):
            row = self.getWidgetPosition(row)[0]
        for role in (QtWidgets.QFormLayout.LabelRole, QtWidgets.QFormLayout.FieldRole):
            item = self.itemAt(row, role)
            if item is not None and item.widget() is not None:
                item.widget().setVisible(visible)

    QtWidgets.QFormLayout.setRowVisible = _set_row_visible
    # Qt 6 moved these widget classes into QtGui.
    QtGui.QAction = QtWidgets.QAction
    QtGui.QActionGroup = QtWidgets.QActionGroup
    QtGui.QShortcut = QtWidgets.QShortcut
    # Keep the shared application code independent of renamed Qt entry points.
    def _exec(self, *args, **kwargs):
        # Do not copy Shiboken's C descriptors: QMenu's overloaded static/instance
        # exec_ otherwise loses its instance binding and can crash the process.
        return self.exec_(*args, **kwargs)

    for cls in (QtCore.QCoreApplication, QtCore.QEventLoop, QtCore.QThread,
                QtWidgets.QApplication, QtWidgets.QDialog, QtWidgets.QMenu,
                QtGui.QDrag):
        if not hasattr(cls, 'exec'):
            cls.exec = _exec
    if not hasattr(QtCore.QLibraryInfo, 'path'):
        QtCore.QLibraryInfo.path = QtCore.QLibraryInfo.location
        QtCore.QLibraryInfo.LibraryPath = QtCore.QLibraryInfo.LibraryLocation
    for cls, old_position in ((QtGui.QMouseEvent, 'localPos'),
                              (QtGui.QEnterEvent, 'localPos'),
                              (QtGui.QHoverEvent, 'posF'),
                              (QtGui.QDropEvent, 'posF'),
                              (QtGui.QWheelEvent, 'posF')):
        if not hasattr(cls, 'position'):
            cls.position = getattr(cls, old_position)
    if not hasattr(QtGui.QMouseEvent, 'globalPosition'):
        QtGui.QMouseEvent.globalPosition = QtGui.QMouseEvent.screenPos

for name, module in (('QtCore', QtCore), ('QtGui', QtGui), ('QtWidgets', QtWidgets)):
    sys.modules[f'{__name__}.{name}'] = module


def configure_application():
    """Apply identical DPI policy before constructing QApplication."""
    if QtCore.QCoreApplication.instance() is not None:
        raise RuntimeError('Qt display policy must be configured before QApplication')
    if BINDING == 'PySide2':
        QtCore.QCoreApplication.setAttribute(QtCore.Qt.AA_EnableHighDpiScaling, True)
        QtCore.QCoreApplication.setAttribute(QtCore.Qt.AA_UseHighDpiPixmaps, True)
    QtGui.QGuiApplication.setHighDpiScaleFactorRoundingPolicy(
        QtCore.Qt.HighDpiScaleFactorRoundingPolicy.PassThrough)


def apply_application_style(app):
    """Use Qt's own widgets so Windows theme/version does not change geometry."""
    app.setStyle('Fusion')
    if sys.platform == 'win32':
        app.setFont(QtGui.QFont('Microsoft YaHei UI', 9))
