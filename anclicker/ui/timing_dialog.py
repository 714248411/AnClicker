"""Advanced execution timing settings dialog."""
from anclicker.execution.execution_timing import *
from anclicker.platform.qt_compat.QtCore import Qt


def open_advanced_timing(parent, database):
    # Keep one owned window and avoid a second nested exec() inside an editor.
    dialog = getattr(parent, '_advanced_timing_dialog', None)
    if dialog is not None:
        dialog.showNormal()
        dialog.raise_()
        dialog.activateWindow()
        return dialog
    dialog = AdvancedTimingDialog(parent, database)
    parent._advanced_timing_dialog = dialog
    dialog.setWindowModality(Qt.WindowModal)
    def finished(_):
        parent._advanced_timing_dialog = None
        dialog.deleteLater()
    dialog.finished.connect(finished)
    dialog.open()
    dialog.raise_()
    dialog.activateWindow()
    return dialog
