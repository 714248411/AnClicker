"""Compatibility alias for anclicker.ui.guided_code_editor."""
import importlib as _importlib
import sys as _sys
_sys.modules[__name__] = _importlib.import_module('anclicker.ui.guided_code_editor')
