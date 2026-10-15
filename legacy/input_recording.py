"""Compatibility alias for anclicker.execution.input_recording."""
import importlib as _importlib
import sys as _sys
_sys.modules[__name__] = _importlib.import_module('anclicker.execution.input_recording')
