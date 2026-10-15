"""Compatibility alias for anclicker.storage.graph_repository."""
import importlib as _importlib
import sys as _sys
_sys.modules[__name__] = _importlib.import_module('anclicker.storage.graph_repository')
