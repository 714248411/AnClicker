"""Compatibility alias for anclicker.execution.agent_provider."""
import importlib as _importlib
import sys as _sys
_sys.modules[__name__] = _importlib.import_module('anclicker.execution.agent_provider')
