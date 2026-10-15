"""Compatibility alias for anclicker.ui.layout_presets."""
import importlib as _importlib
import sys as _sys
_sys.modules[__name__] = _importlib.import_module('anclicker.ui.layout_presets')
