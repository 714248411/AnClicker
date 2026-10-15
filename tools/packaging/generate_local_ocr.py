"""Generate OCR editor adapters/bindings from maintained schemas and UI sources."""
from pathlib import Path
import sys

import sys as _import_sys
from pathlib import Path as _ImportPath
if __package__ in (None, ""):
    _import_sys.path.insert(0, str(_ImportPath(__file__).resolve().parents[2]))
from anclicker._imports import DeferredImports as _DeferredImports

# Dependencies declared here retain their existing on-demand loading boundaries.
_module_imports = _DeferredImports(globals(), {
    'main': ('from', 'tools.generate_instruction_adapters', ('main',), 0),
})

ROOT = Path(__file__).resolve().parents[2]
sys.path.insert(0, str(ROOT))
main = _module_imports.load('main')

if __name__ == '__main__':
    main('ocr')
