"""Compatibility alias for models.agent_service_lock."""
import importlib as _importlib
import sys as _sys
_sys.modules[__name__] = _importlib.import_module('models.agent_service_lock')
