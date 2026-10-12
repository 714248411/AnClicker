"""Run Qt regression tests using the native Windows platform plugin."""
import os
import sys
from pathlib import Path
os.environ['QT_QPA_PLATFORM'] = 'windows' if os.name == 'nt' else 'offscreen'
os.environ.setdefault('PYTHONUTF8','1')
sys.path.insert(0,str(Path(__file__).resolve().parents[1]))
import pytest
raise SystemExit(pytest.main(sys.argv[1:]))
