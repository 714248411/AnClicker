"""Compatibility entry point for models.prepare_agent_models."""
import runpy
import importlib
import sys
from pathlib import Path
ROOT = Path(__file__).resolve().parents[1]
if __name__ == '__main__':
    sys.path.insert(0, str(ROOT))
    runpy.run_module('models.prepare_agent_models', run_name='__main__')
else:
    sys.modules[__name__] = importlib.import_module('models.prepare_agent_models')
