"""Compatibility alias for anclicker.app.startup_environment."""
import importlib as _importlib
import sys as _sys
_sys.modules[__name__] = _importlib.import_module('anclicker.app.startup_environment')
