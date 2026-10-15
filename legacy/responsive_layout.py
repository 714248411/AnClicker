"""Compatibility alias for anclicker.ui.responsive_layout."""
import importlib as _importlib
import sys as _sys
_sys.modules[__name__] = _importlib.import_module('anclicker.ui.responsive_layout')
