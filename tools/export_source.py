"""Export source without runtime data, credentials, caches or built binaries."""
import argparse
import hashlib
import os
from pathlib import Path
import zipfile
import sys

import sys as _import_sys
from pathlib import Path as _ImportPath
if __package__ in (None, ""):
    _import_sys.path.insert(0, str(_ImportPath(__file__).resolve().parents[1]))
from anclicker._imports import DeferredImports as _DeferredImports

# Dependencies declared here retain their existing on-demand loading boundaries.
_module_imports = _DeferredImports(globals(), {
    'anclicker': ('import', 'anclicker', (), False),
    'CURRENT_VERSION': ('from', 'info', ('CURRENT_VERSION',), 0),
})

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT))
anclicker = _module_imports.load('anclicker')  # Enable source-tree legacy entry points.
CURRENT_VERSION = _module_imports.load('CURRENT_VERSION')
folders = {'anclicker', 'legacy', 'resources', '.config', '.github', '.gitee', 'docs', 'examples', 'archive', 'integrations', 'tools'}
skip = {'__pycache__', 'node_modules', '.pytest_cache', '.git', '.private-agent', 'private_agent', 'anclicker_private_agent'}
diagnostics = {'inspect_defaults.py', 'inspect_update_sdk.py', 'probe_conversion.py', 'check_hao123.py'}
parser = argparse.ArgumentParser(description=__doc__)
parser.add_argument('--output', type=Path, default=ROOT / 'artifacts/dist/source' / f'AnClicker-{CURRENT_VERSION}-win-DaiMa.zip')
args = parser.parse_args()
target = args.output.resolve()
target.parent.mkdir(parents=True, exist_ok=True)
files = [p for p in ROOT.iterdir() if p.is_file() and (p.suffix.lower() in {'.py', '.md', '.toml', '.lock', '.txt', '.qrc', '.ico', '.cmd'} or p.name in {'LICENSE', '.gitignore', '.python-version'})]

for folder in sorted(folders):
    for current, dirs, names in os.walk(ROOT / folder):
        dirs[:] = [d for d in dirs if d not in skip]
        for name in names:
            path = Path(current) / name
            if name in diagnostics or path.suffix.lower() in {'.pyc', '.db', '.log', '.exe', '.dll', '.pyd'}:
                continue
            files.append(path)
with zipfile.ZipFile(target, 'x', compression=zipfile.ZIP_DEFLATED) as archive:
    for path in sorted(files):
        if path.name.startswith(('agent_api', 'private_agent')) or '.private.' in path.name:
            raise RuntimeError('Private Agent source must not be placed inside the public source tree: '+str(path))
        archive.write(path, str(Path('AnClicker-' + CURRENT_VERSION) / path.relative_to(ROOT)))
digest = hashlib.sha256(target.read_bytes()).hexdigest()
target.with_suffix(target.suffix + '.sha256').write_text(digest + '  ' + target.name + '\n', encoding='ascii')
print(f'Source exported: {len(files)} files; {target.stat().st_size} bytes; {digest}')
