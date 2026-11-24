"""Compatibility alias for models.agent_model_validation."""
import importlib as _importlib
import sys as _sys
_sys.modules[__name__] = _importlib.import_module('models.agent_model_validation')
