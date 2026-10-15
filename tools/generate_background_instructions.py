"""Compatibility entrypoint for background adapter/UI generation."""

import sys as _import_sys
from pathlib import Path as _ImportPath
if __package__ in (None, ""):
    _import_sys.path.insert(0, str(_ImportPath(__file__).resolve().parents[1]))
from anclicker._imports import DeferredImports as _DeferredImports

# Dependencies declared here retain their existing on-demand loading boundaries.
_module_imports = _DeferredImports(globals(), {
    'main': ('from', 'generate_instruction_adapters', ('main',), 1),
    'main_2': ('from', 'generate_instruction_adapters', ('main',), 0),
})

if __package__:
    main = _module_imports.load('main')
else:
    main = _module_imports.load('main_2')

if __name__ == "__main__":
    main('background')
