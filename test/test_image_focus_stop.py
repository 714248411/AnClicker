from types import SimpleNamespace
from unittest.mock import Mock, patch

from instructions.common import actions
from instructions.models import ExecutionContext, CommandRecord
from instructions.registry import get_instruction_spec


def stop_on_wait(context):
    def wait(seconds, actual):
        assert actual is context
        if seconds > 0:
            context.stop_requested = True
            return False
        return not context.stop_requested
    context.metadata['wait_interruptibly'] = wait


def test_long_image_search_can_stop_and_keeps_resolved_project_path():
    context = ExecutionContext()
    stop_on_wait(context)
    locator = Mock(return_value=None)
    with patch.object(actions, 'resolve_image_path', return_value='resolved/中文.png'), \
         patch.object(actions, 'pyautogui_module', return_value=SimpleNamespace(locateCenterOnScreen=locator)):
        assert actions.locate_image({'图像路径': 'relative.png'}, context, min_search_time=60) is None
    assert context.stop_requested
    locator.assert_called_once()
    assert locator.call_args.args[0] == 'resolved/中文.png'
    assert locator.call_args.kwargs['minSearchTime'] == 0


def test_stop_during_image_capture_never_clicks_late_result():
    context = ExecutionContext()
    def capture(*args, **kwargs):
        context.stop_requested = True
        return SimpleNamespace(x=10, y=20)
    gui = SimpleNamespace(locateCenterOnScreen=capture, moveTo=Mock(), click=Mock())
    with patch.object(actions, 'resolve_image_path', return_value='image.png'), \
         patch.object(actions, 'pyautogui_module', return_value=gui):
        assert get_instruction_spec('图像点击').create_executor().execute(context,
            CommandRecord(1, '图像点击', {'图像路径': 'image.png'})) is False
    gui.moveTo.assert_not_called()
    gui.click.assert_not_called()


def test_long_focus_poll_stops_without_next_native_read():
    context = ExecutionContext()
    stop_on_wait(context)
    gui = SimpleNamespace(getActiveWindowTitle=Mock(return_value='different'))
    with patch.object(actions, 'pyautogui_module', return_value=gui):
        result = get_instruction_spec('窗口焦点等待').create_executor().execute(context,
            CommandRecord(1, '窗口焦点等待', {'标题包含': 'target', '检测频率': 60, '等待时间': 600}))
    assert result is None and context.stop_requested
    gui.getActiveWindowTitle.assert_called_once()


def test_stopped_context_does_not_start_another_instruction_repeat():
    service = Mock()
    context = ExecutionContext(stop_requested=True, services={'文本输入': service})
    get_instruction_spec('文本输入').create_executor().execute(context, CommandRecord(1, '文本输入', {}, repeat_count=10))
    service.assert_not_called()
