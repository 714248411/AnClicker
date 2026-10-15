"""Compatibility alias for anclicker.execution.flow_jump_runtime."""
import importlib as _importlib
import sys as _sys
_sys.modules[__name__] = _importlib.import_module('anclicker.execution.flow_jump_runtime')
