"""Compatibility alias for anclicker.domain.web_urls."""
import importlib as _importlib
import sys as _sys
_sys.modules[__name__] = _importlib.import_module('anclicker.domain.web_urls')
