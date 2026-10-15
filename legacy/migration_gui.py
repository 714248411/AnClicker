"""Compatibility alias for anclicker.ui.migration_gui."""
import importlib as _importlib
import sys as _sys
_sys.modules[__name__] = _importlib.import_module('anclicker.ui.migration_gui')
