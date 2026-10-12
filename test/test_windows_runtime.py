import ctypes
import sys
import pytest
from types import SimpleNamespace
from unittest.mock import Mock

from windows_runtime import configure_dpi

pytestmark = pytest.mark.skipif(sys.platform != 'win32', reason='Windows ctypes last-error API')


def test_1607_uses_per_monitor_when_v2_is_rejected():
    setter = Mock(side_effect=[False, True])
    user32 = SimpleNamespace(SetProcessDpiAwarenessContext=setter)
    assert configure_dpi(user32) == 'per-monitor'
    assert [call.args for call in setter.call_args_list] == [(-4,), (-3,)]


def test_missing_context_api_uses_shcore():
    setter = Mock(return_value=0)
    assert configure_dpi(SimpleNamespace(), SimpleNamespace(SetProcessDpiAwareness=setter)) == 'per-monitor'
    setter.assert_called_once_with(2)


def test_manifest_policy_is_respected():
    def denied(_):
        ctypes.set_last_error(5)
        return False
    setter = Mock(side_effect=denied)
    shcore = SimpleNamespace(SetProcessDpiAwareness=Mock())
    assert configure_dpi(SimpleNamespace(SetProcessDpiAwarenessContext=setter), shcore) == 'existing-policy'
    assert setter.call_count == 1
    shcore.SetProcessDpiAwareness.assert_not_called()
