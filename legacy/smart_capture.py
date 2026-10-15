"""Compatibility alias for anclicker.ui.smart_capture."""
import importlib as _importlib
import sys as _sys
_sys.modules[__name__] = _importlib.import_module('anclicker.ui.smart_capture')
