"""Compatibility alias for anclicker.domain.instructions."""
import importlib as _importlib
import sys as _sys
_sys.modules[__name__] = _importlib.import_module('anclicker.domain.instructions')
