"""AnClicker components and source-tree compatibility bootstrap."""
from pathlib import Path
import sys


def enable_legacy_imports():
    """Expose historical top-level imports from their dedicated directory.

    Frozen builds collect those modules explicitly and do not need this path.
    The directory is appended so modern modules always take precedence.
    """
    legacy = Path(__file__).resolve().parent.parent / 'legacy'
    if legacy.is_dir() and str(legacy) not in sys.path:
        sys.path.append(str(legacy))


enable_legacy_imports()
