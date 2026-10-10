"""Guard the actual manifest handed to PyInstaller against 1607 regressions."""
import importlib.util
from pathlib import Path
import pytest

ROOT = Path(__file__).resolve().parents[1]
spec = importlib.util.spec_from_file_location('windows_compatibility', ROOT / 'packaging/windows_compatibility.py')
module = importlib.util.module_from_spec(spec)
spec.loader.exec_module(module)


def test_shipping_manifest_has_1607_fallback():
    module.validate_manifest((ROOT / 'packaging/windows.manifest').read_bytes())


@pytest.mark.parametrize('replacement', ['PerMonitorV2', 'PerMonitorV2, unaware', 'system'])
def test_reject_manifest_without_per_monitor_fallback(replacement):
    manifest = (ROOT / 'packaging/windows.manifest').read_text(encoding='utf-8')
    with pytest.raises(RuntimeError, match='1607'):
        module.validate_manifest(manifest.replace('PerMonitorV2, PerMonitor', replacement))
