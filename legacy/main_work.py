"""Compatibility alias for anclicker.app.main_work."""
import importlib as _importlib
import sys as _sys
_sys.modules[__name__] = _importlib.import_module('anclicker.app.main_work')
