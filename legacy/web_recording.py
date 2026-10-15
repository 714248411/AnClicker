"""Compatibility alias for anclicker.execution.web_recording."""
import importlib as _importlib
import sys as _sys
_sys.modules[__name__] = _importlib.import_module('anclicker.execution.web_recording')
