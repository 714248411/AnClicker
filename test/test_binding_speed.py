"""Fast input-only binds must remain background-only and safe to reuse."""
from unittest.mock import Mock
from types import SimpleNamespace
import pytest
from background_binding import binding_attempts
from background_runtime import bind_background, close_background, current_backend, ERROR
from instructions.models import ExecutionContext, InstructionDraft
from instructions.registry import get_instruction_spec
from test.test_background_runtime import Windows, Transport
from test.test_background_presets import app


@pytest.fixture
def ctx():
    context = ExecutionContext(services={'background_windows': Windows, 'background_transport': Transport})
    yield context
    close_background(context)


def test_input_only_skips_capture_and_keeps_dx_mouse_keyboard(ctx):
    bind_background(ctx, {'启用截图': False})
    session = current_backend(ctx)
    assert session.transport.calls[0] == ('BindWindow', (123, 'normal', 'dx', 'dx', 0))
    assert not any(name == 'Capture' for name, args in session.transport.calls)
    session.click(1, 2)
    assert any(name == 'LeftClick' for name, args in session.transport.calls)
    for action in (session.screenshot, lambda: session.pixel(1, 2)):
        with pytest.raises(RuntimeError, match='截图'):
            action()


def test_identical_bind_reuses_session_without_wait_or_capture(ctx):
    bind_background(ctx, {})
    first = current_backend(ctx)
    before = list(first.transport.calls)
    first._wait = Mock(side_effect=AssertionError('should not wait'))
    bind_background(ctx, {})
    assert current_backend(ctx) is first
    assert first.transport.calls == before


@pytest.mark.parametrize('change', ['capture', 'window', 'host', 'held_key'])
def test_changed_or_unhealthy_binding_does_not_reuse(ctx, change):
    bind_background(ctx, {})
    first = current_backend(ctx)
    params = {}
    if change == 'capture':
        params['启用截图'] = False
    elif change == 'window':
        class OtherWindow(Windows):
            target = dict(Windows.target, 窗口句柄='456')
        ctx.services['background_windows'] = OtherWindow
    elif change == 'host':
        first.transport.process = SimpleNamespace(poll=lambda: 1)
    else:
        first.keyDown('ctrl')
    bind_background(ctx, params)
    assert current_backend(ctx) is not first and first.closed and first.transport.closed
    if change == 'held_key':
        assert ('KeyUp', (17,)) in first.transport.calls


@pytest.mark.parametrize('params,stop', [({'绑定方案': 'invalid'}, False), ({}, True)])
def test_invalid_or_cancelled_rebind_cleans_previous_session(ctx, params, stop):
    bind_background(ctx, {})
    old = current_backend(ctx)
    ctx.stop_requested = stop
    with pytest.raises((RuntimeError, ValueError)):
        bind_background(ctx, params)
    assert old.closed and old.transport.closed and ERROR in ctx.metadata


def test_successful_fallback_is_remembered_when_worker_must_restart(ctx):
    created = []
    class Retry(Transport):
        def __init__(self, context):
            super().__init__(context)
            created.append(self)
        def call(self, name, *args, **kwargs):
            result = super().call(name, *args, **kwargs)
            if name == 'BindWindow' and args[1] == 'dx':
                return 0
            return result
    ctx.services['background_transport'] = Retry
    bind_background(ctx, {})
    current_backend(ctx).transport.process = SimpleNamespace(poll=lambda: 1)
    previous = len(created)
    bind_background(ctx, {})
    assert len(created) == previous + 1
    assert created[-1].calls[0][1][1] == 'dx2'


@pytest.mark.parametrize('value', ['false', 0, None, []])
def test_invalid_capture_flag_is_not_silently_enabled(value):
    with pytest.raises(ValueError):
        binding_attempts({'启用截图': value})


def test_capture_setting_roundtrips_and_old_projects_keep_capture(app):
    editor = get_instruction_spec('绑定选择窗口').create_editor()
    try:
        assert editor.capture_enabled.isChecked()
        editor.capture_enabled.setChecked(False)
        draft = editor.get_draft()
        assert draft.parameters['启用截图'] is False
        editor.load_draft(draft)
        assert not editor.capture_enabled.isChecked()
        editor.load_draft(InstructionDraft('绑定选择窗口', {}))
        assert editor.capture_enabled.isChecked()
    finally:
        editor.deleteLater()


def test_caption_only_change_does_not_restart_same_window(ctx):
    bind_background(ctx, {})
    old = current_backend(ctx)
    class RenamedWindow(Windows):
        target = dict(Windows.target, 窗口标题='已更新内容')
    ctx.services['background_windows'] = RenamedWindow
    bind_background(ctx, {})
    assert current_backend(ctx) is old
