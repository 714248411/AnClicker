"""Compatibility alias for models.agent_small_model."""
import importlib as _importlib
import sys as _sys
_sys.modules[__name__] = _importlib.import_module('models.agent_small_model')
