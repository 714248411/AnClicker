"""Compatibility alias for anclicker.execution.recorded_input."""
import importlib as _importlib
import sys as _sys
_sys.modules[__name__] = _importlib.import_module('anclicker.execution.recorded_input')
