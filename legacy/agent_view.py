"""Compatibility alias for anclicker.ui.agent_view."""
import importlib as _importlib
import sys as _sys
_sys.modules[__name__] = _importlib.import_module('anclicker.ui.agent_view')
