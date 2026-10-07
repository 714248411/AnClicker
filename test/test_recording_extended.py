"""Exercise capture and replay without injecting any input into the user's desktop."""
import os
os.environ.setdefault("QT_QPA_PLATFORM", "offscreen")
from types import SimpleNamespace
from unittest.mock import Mock, patch

import pytest
from PySide6.QtWidgets import QApplication, QMainWindow
from input_recording import GlobalInputRecorder, RecordingBuffer, InputEvent, events_to_drafts, recording_key
from recorded_input import windows_key_parameters, key_event, button_event, scroll_event
from instructions.common.actions import release_recorded_inputs
from instructions.models import CommandRecord, ExecutionContext
from instructions.registry import get_instruction_spec
from recording_view import RecordingView


@pytest.fixture
def capture():
    listeners = []
    class Listener:
        def __init__(self, **callbacks):
            self.callbacks = callbacks
            listeners.append(self)
        def start(self): pass
        def stop(self): pass
        def join(self, timeout): pass
    pynput = SimpleNamespace(keyboard=SimpleNamespace(Listener=Listener),
                             mouse=SimpleNamespace(Listener=Listener))
    buffer = RecordingBuffer()
    buffer.start()
    recorder = GlobalInputRecorder(buffer, Mock(), Mock())
    with patch.dict("sys.modules", {"pynput": pynput,
                                    "pyautogui": SimpleNamespace(KEYBOARD_KEYS=["a", "f8"])}), \
         patch("input_recording.sys.platform", "win32"):
        recorder.start()
        yield recorder, buffer, listeners
        recorder.stop()


@pytest.mark.parametrize("vk,scan,extended", [
    (0x0D, 0x1C, 0), (0x0D, 0x1C, 1),  # Enter vs keypad Enter
    (0xA2, 0x1D, 0), (0xA3, 0x1D, 1),  # left/right Ctrl
    (0xA0, 0x2A, 0), (0xA1, 0x36, 0),
    (0xA4, 0x38, 0), (0xA5, 0x38, 1),
    (0x60, 0x52, 0), (0x2D, 0x52, 1),  # numpad 0 vs Insert
    (0xB3, 0, 1), (0xAF, 0, 1), (0xA6, 0, 1),  # media/browser
    (0x87, 0x76, 0), (0x13, 0x45, 0), (0x2C, 0x37, 1),
])
def test_windows_raw_special_keys_preserve_physical_identity(capture, vk, scan, extended):
    recorder, buffer, listeners = capture
    callback = listeners[0].callbacks["win32_event_filter"]
    for msg in (0x104, 0x104, 0x105):  # auto-repeat is preserved
        assert callback(msg, SimpleNamespace(vkCode=vk, scanCode=scan, flags=extended)) is False
    token = f"win32:{vk}:{scan}:{extended}"
    assert [e.data for e in buffer.snapshot()] == [(token, True), (token, True), (token, False)]
    recorder.failed.assert_not_called()
    drafts = events_to_drafts(buffer.snapshot())
    context = ExecutionContext()
    with patch("recorded_input.send_windows_key") as send, \
         patch("instructions.common.actions.pyautogui_module", return_value=Mock()):
        for draft in drafts:
            get_instruction_spec(draft.type_id).create_executor().execute(
                context, CommandRecord(1, draft.type_id, draft.parameters))
    assert [call.args for call in send.call_args_list] == [(token, True), (token, True), (token, False)]
    assert context.metadata["recorded_keys"] == set()


def test_f8_can_be_recorded_or_used_to_stop(capture):
    recorder, buffer, listeners = capture
    callback = listeners[0].callbacks["win32_event_filter"]
    data = SimpleNamespace(vkCode=0x77, scanCode=0x42, flags=0)
    recorder.stop_with_f8 = False
    callback(0x100, data)
    callback(0x101, data)
    assert len(buffer.snapshot()) == 2
    recorder.stopped.assert_not_called()
    recorder.stop_with_f8 = True
    callback(0x100, data)
    recorder.stopped.assert_called_once()
    assert not recorder.active
    assert len(buffer.snapshot()) == 2


@pytest.mark.parametrize("raw_windows", [True, False])
@pytest.mark.parametrize("f8_enabled", [True, False])
def test_escape_always_stops_and_is_not_recorded(capture, raw_windows, f8_enabled):
    recorder, buffer, listeners = capture
    recorder.stop_with_f8 = f8_enabled
    recorder.exclude_keyboard = lambda: True
    cb = listeners[0].callbacks
    if raw_windows:
        cb["win32_event_filter"](0x100, SimpleNamespace(vkCode=0x1B, scanCode=1, flags=0))
    else:
        cb["on_press"](SimpleNamespace(name="esc"))
    recorder.stopped.assert_called_once()
    assert not recorder.active
    assert not buffer.active
    assert buffer.snapshot() == ()


def test_stop_button_and_escape_cancel_countdown_without_hooks():
    app = QApplication.instance() or QApplication([])
    window = QMainWindow()
    window.command_thread = SimpleNamespace(isRunning=lambda: False)
    view = RecordingView(window)
    with patch("recording_view.GlobalInputRecorder") as backend:
        view.begin()
        view.stop_button.click()
        assert not view.busy
        view.begin()
        view.escape_shortcut.activated.emit()
        assert not view.busy
        backend.assert_not_called()
    window.close()


def test_side_buttons_horizontal_and_precision_wheel(capture):
    recorder, buffer, listeners = capture
    mouse = listeners[1].callbacks
    mouse["on_click"](10, 20, SimpleNamespace(name="x1"), True)
    recorder.exclude_mouse = lambda x, y: True
    mouse["on_move"](30, 40)
    mouse["on_click"](30, 40, SimpleNamespace(name="x1"), False)
    recorder.exclude_mouse = lambda x, y: False
    for msg, delta in ((0x20A, -30), (0x20E, 60)):
        mouse["win32_event_filter"](msg, SimpleNamespace(
            mouseData=(delta & 0xFFFF) << 16, pt=SimpleNamespace(x=30, y=40)))
    drafts = events_to_drafts(buffer.snapshot())
    assert drafts[0].parameters["录制鼠标键"] == "x1"
    assert drafts[1].type_id == "鼠标拖拽"
    assert drafts[2].parameters["录制动作"] == "松开"
    assert drafts[3].parameters["录制滚轮"] == [0, -.25]
    assert drafts[4].parameters["录制滚轮"] == [.5, 0]
    recorder.failed.assert_not_called()


def test_key_release_survives_focus_change(capture):
    recorder, buffer, listeners = capture
    cb = listeners[0].callbacks
    cb["on_press"](SimpleNamespace(vk=65, char="a"))
    recorder.exclude_keyboard = lambda: True
    cb["on_release"](SimpleNamespace(vk=65, char="a"))
    assert [e.data for e in buffer.snapshot()] == [("a", True), ("a", False)]


def test_native_fallbacks_and_cleanup():
    ctx, gui = ExecutionContext(), Mock(FAILSAFE=True)
    keyboard = SimpleNamespace(Key=SimpleNamespace(media_volume_up="media"),
                               KeyCode=SimpleNamespace(from_vk=Mock(return_value="vk"),
                                                       from_char=Mock(return_value="char")))
    mouse = SimpleNamespace(Button=SimpleNamespace(x1="side1", x2="side2"))
    kc, mc = Mock(), Mock()
    with patch("recorded_input.keyboard_controller", return_value=(keyboard, kc)), \
         patch("recorded_input.mouse_controller", return_value=(mouse, mc)), \
         patch("recorded_input.send_windows_key") as send, \
         patch("instructions.common.actions.pyautogui_module", return_value=gui):
        key_event(ctx, "special:media_volume_up", True, gui)
        kc.press.assert_called_with("media")
        key_event(ctx, "char:中", True, gui)
        kc.press.assert_called_with("char")
        button_event(ctx, "x2", True, gui)
        mc.press.assert_called_with("side2")
        scroll_event(ctx, -.5, 2)
        mc.scroll.assert_called_with(-.5, 2)
        ctx.metadata.update(recorded_keys={"win32:163:29:1", "special:media_volume_up"},
                            recorded_buttons={"x2"})
        release_recorded_inputs(ctx)
        send.assert_called_once_with("win32:163:29:1", False)
        mc.release.assert_called_with("side2")
        kc.release.assert_called_with("media")
        assert gui.FAILSAFE


def test_windows_parameters_do_not_collapse_keypad_or_unicode():
    assert windows_key_parameters("win32:13:28:1", True) == dict(wVk=0, wScan=28, dwFlags=9)
    assert windows_key_parameters("win32:13:28:0", False) == dict(wVk=0, wScan=28, dwFlags=10)
    assert windows_key_parameters("win32:231:20013:0", False) == dict(wVk=0, wScan=20013, dwFlags=6)
    assert windows_key_parameters("win32:19:69:0", True)["wVk"] == 19
    with pytest.raises(ValueError):
        windows_key_parameters("win32:999:1:0", True)


def test_fallback_key_names():
    assert recording_key(SimpleNamespace(name="media_volume_up"), [], "linux") == "special:media_volume_up"
    assert recording_key(SimpleNamespace(vk=96, char="0"), ["0"], "win32") == "native:win32:96"
    assert recording_key(SimpleNamespace(vk=999, char=None), [], "linux") == "native:linux:999"


@pytest.mark.skipif(os.name != "nt", reason="Windows native API structure test")
def test_native_sendinput_structure_and_rejection_without_injection():
    from recorded_input import send_windows_key
    with patch("pynput._util.win32.SendInput", return_value=1) as send:
        send_windows_key("win32:13:28:1", True)
        event = send.call_args.args[1]._obj
        assert event.value.ki.wScan == 28
        assert event.value.ki.dwFlags == 9
        send.return_value = 0
        with pytest.raises(RuntimeError, match="系统拒绝"):
            send_windows_key("win32:13:28:1", False)


def test_extended_recording_database_and_workbook_roundtrip(tmp_path):
    from 数据库操作 import DatabaseOperation
    from graph_repository import GraphRepository
    from openpyxl import Workbook
    db = DatabaseOperation(str(tmp_path / "original.db"))
    repo = GraphRepository(db.db_path)
    events = [InputEvent(0, "key", ("win32:163:29:1", True)),
              InputEvent(.1, "button", (-100, 200, "x2", True)),
              InputEvent(.2, "move", (-200, 300)),
              InputEvent(.3, "scroll", (-200, 300, -.5, .25))]
    drafts = events_to_drafts(events)
    repo.append_recording(drafts, connect=True)
    wb = Workbook()
    repo.export_to_workbook(wb, db)
    restored_db = DatabaseOperation(str(tmp_path / "restored.db"))
    restored = GraphRepository(restored_db.db_path)
    restored.import_from_workbook(wb)
    assert [c.parameters for c in restored.execution_snapshot().commands] == [d.parameters for d in drafts]
    restored.validate_graph()


def test_special_inputs_editor_preserves_replay_metadata():
    app = QApplication.instance() or QApplication([])
    drafts = events_to_drafts([InputEvent(0, "button", (10, 20, "x2", True)),
                              InputEvent(.1, "scroll", (10, 20, -1, .5)),
                              InputEvent(.2, "key", ("win32:13:28:1", True))])
    for draft in drafts:
        editor = get_instruction_spec(draft.type_id).create_editor(draft=draft)
        edited = editor.get_draft()
        for key, value in draft.parameters.items():
            if key.startswith("录制"):
                assert edited.parameters[key] == value
        editor.close()
    window = QMainWindow()
    window.command_thread = SimpleNamespace(isRunning=lambda: False)
    view = RecordingView(window)
    view.f8_option.setChecked(False)
    assert not view.hide_option.isChecked()
    assert not view.hide_option.isEnabled()
    window.close()
