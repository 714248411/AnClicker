"""Export source without runtime data, credentials, caches or built binaries."""
import hashlib
import os
from pathlib import Path
import zipfile
import sys
ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT))
from info import CURRENT_VERSION
folders = {'.config', '.github', '.gitee', 'docs', 'flat', 'instructions', 'integrations', 'node_editor', 'node_test', 'old_ins', 'packaging', 'qt_compat', 'test', 'tools', 'update', 'Window', 'WindowControl', 'wxocr_client'}
skip = {'__pycache__', 'node_modules', '.pytest_cache', '.git'}
diagnostics = {'inspect_defaults.py', 'inspect_update_sdk.py', 'probe_conversion.py', 'check_hao123.py'}
target = ROOT.parent / f'AnClicker-{CURRENT_VERSION}-win-DaiMa.zip'
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
        archive.write(path, str(Path('AnClicker-' + CURRENT_VERSION) / path.relative_to(ROOT)))
digest = hashlib.sha256(target.read_bytes()).hexdigest()
target.with_suffix(target.suffix + '.sha256').write_text(digest + '  ' + target.name + '\n', encoding='ascii')
print(f'Source exported: {len(files)} files; {target.stat().st_size} bytes; {digest}')
