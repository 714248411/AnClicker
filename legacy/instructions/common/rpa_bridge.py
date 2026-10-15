"""Compatibility alias for anclicker.platform.rpa_bridge."""
import importlib as _importlib
import sys as _sys
_sys.modules[__name__] = _importlib.import_module('anclicker.platform.rpa_bridge')
