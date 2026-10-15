"""Compatibility timing API and lazily loaded dialog."""
from anclicker.execution.execution_timing import *

import sys as _import_sys
from pathlib import Path as _ImportPath
if __package__ in (None, ""):
    _import_sys.path.insert(0, str(_ImportPath(__file__).resolve().parents[1]))
from anclicker._imports import DeferredImports as _DeferredImports

# Dependencies declared here retain their existing on-demand loading boundaries.
_module_imports = _DeferredImports(globals(), {
    'open_advanced_timing': ('from', 'anclicker.ui.timing_dialog', ('open_advanced_timing',), 0),
})


def __getattr__(name):
    if name == "open_advanced_timing":
        open_advanced_timing = _module_imports.load('open_advanced_timing')
        return open_advanced_timing
    raise AttributeError(name)
