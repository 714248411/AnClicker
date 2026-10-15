"""Compatibility alias for anclicker.platform.background_preload."""
import importlib as _importlib
import sys as _sys
_sys.modules[__name__] = _importlib.import_module('anclicker.platform.background_preload')
