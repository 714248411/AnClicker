"""Advanced execution timing settings dialog."""
from anclicker.execution.execution_timing import *

def open_advanced_timing(parent, database):
    dialog = AdvancedTimingDialog(parent, database)
    return dialog.exec()
