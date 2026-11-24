"""Stage the standalone worker's storage imports in the current candidate."""
import shutil
from pathlib import Path

root = Path(__file__).resolve().parents[1]
for name in ('__init__.py', 'portable_migration.py'):
    source = root / 'anclicker/storage' / name
    target = root / 'artifacts/dist/v1.9.2/AnClicker/anclicker/storage' / name
    target.parent.mkdir(parents=True, exist_ok=True)
    shutil.copy2(source, target)
