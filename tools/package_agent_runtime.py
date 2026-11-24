"""Compatibility entry point for models.package_agent_runtime."""
import runpy
import importlib
import sys
from pathlib import Path
ROOT = Path(__file__).resolve().parents[1]
if __name__ == '__main__':
    sys.path.insert(0, str(ROOT))
    runpy.run_module('models.package_agent_runtime', run_name='__main__')
else:
    sys.modules[__name__] = importlib.import_module('models.package_agent_runtime')
