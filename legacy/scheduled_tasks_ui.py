"""Compatibility alias for anclicker.ui.scheduled_tasks_ui."""
import importlib as _importlib
import sys as _sys
_sys.modules[__name__] = _importlib.import_module('anclicker.ui.scheduled_tasks_ui')
