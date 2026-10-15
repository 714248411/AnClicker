"""Compatibility alias for anclicker.platform.local_ocr."""
import importlib as _importlib
import sys as _sys
_sys.modules[__name__] = _importlib.import_module('anclicker.platform.local_ocr')
