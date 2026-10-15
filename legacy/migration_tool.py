"""Compatibility import and command-line entrypoint."""

import sys as _import_sys
from pathlib import Path as _ImportPath
if __package__ in (None, ""):
    _import_sys.path.insert(0, str(_ImportPath(__file__).resolve().parents[1]))
from anclicker._imports import DeferredImports as _DeferredImports

# Dependencies declared here retain their existing on-demand loading boundaries.
_module_imports = _DeferredImports(globals(), {
    'runpy': ('import', 'runpy', (), False),
    'importlib': ('import', 'importlib', (), False),
    'sys': ('import', 'sys', (), False),
})

if __name__ == "__main__":
    runpy = _module_imports.load('runpy')
    runpy.run_module('anclicker.storage.migration_tool', run_name="__main__")
else:
    importlib = _module_imports.load('importlib')
    sys = _module_imports.load('sys')
    sys.modules[__name__] = importlib.import_module('anclicker.storage.migration_tool')
