"""Compatibility alias for anclicker.platform.windows_runtime."""
import importlib as _importlib
import sys as _sys
_sys.modules[__name__] = _importlib.import_module('anclicker.platform.windows_runtime')
