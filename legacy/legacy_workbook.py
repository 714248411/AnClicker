"""Compatibility alias for anclicker.storage.legacy_workbook."""
import importlib as _importlib
import sys as _sys
_sys.modules[__name__] = _importlib.import_module('anclicker.storage.legacy_workbook')
