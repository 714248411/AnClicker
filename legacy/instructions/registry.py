"""Compatibility alias for anclicker.instructions.registry."""
import importlib as _importlib
import sys as _sys
_sys.modules[__name__] = _importlib.import_module('anclicker.instructions.registry')
