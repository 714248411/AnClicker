"""Run a historical Python script name after source directory consolidation."""
from pathlib import Path
import runpy
import sys

import sys as _import_sys
from pathlib import Path as _ImportPath
if __package__ in (None, ""):
    _import_sys.path.insert(0, str(_ImportPath(__file__).resolve().parents[1]))
from anclicker._imports import DeferredImports as _DeferredImports

# Dependencies declared here retain their existing on-demand loading boundaries.
_module_imports = _DeferredImports(globals(), {
    'anclicker': ('import', 'anclicker', (), False),
})


ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT))
anclicker = _module_imports.load('anclicker')  # Register the legacy Python module search path.


def main():
    if len(sys.argv) < 2:
        raise SystemExit('Usage: python tools/run_legacy.py <old-script.py> [arguments]')
    old = Path(sys.argv[1].replace('\\', '/'))
    if old.is_absolute() or '..' in old.parts or old.suffix != '.py':
        raise SystemExit('Expected a repository-relative historical Python script')
    if old.parts[0] == 'packaging':
        target = ROOT / 'tools' / old
    elif old.parts[0] == 'node_test':
        target = ROOT / 'examples/node_editor' / Path(*old.parts[1:])
    else:
        target = ROOT / 'legacy' / old
    if not target.is_file():
        raise SystemExit(f'No compatibility entry: {old}')
    sys.path.insert(0, str(target.parent))
    sys.argv = [str(target), *sys.argv[2:]]
    runpy.run_path(str(target), run_name='__main__')


if __name__ == '__main__':
    main()
