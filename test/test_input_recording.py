import os
os.environ.setdefault("QT_QPA_PLATFORM", "offscreen")
import tempfile
import unittest
from types import SimpleNamespace
from unittest.mock import Mock, patch

from openpyxl import Workbook
from PySide6.QtCore import QObject, Signal
from PySide6.QtWidgets import QApplication, QMainWindow, QTableWidget, QLabel, QPlainTextEdit
from graph_repository import GraphRepository
from input_recording import RecordingBuffer, InputEvent, events_to_drafts, normalize_key, GlobalInputRecorder
from instructions.models import CommandRecord, ExecutionContext, InstructionDraft
from instructions.registry import get_instruction_spec
from instructions.common.actions import release_recorded_inputs
from recording_view import RecordingView
from main_work import CommandThread
from view_workspace import ViewWorkspace
from 数据库操作 import DatabaseOperation


class RecordingTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.app = QApplication.instance() or QApplication([])

    def setUp(self):
        self.directory = tempfile.TemporaryDirectory()
        self.database = DatabaseOperation(os.path.join(self.directory.name, "recording.db"))
        self.repository = GraphRepository(self.database.db_path)

    def tearDown(self):
        self.directory.cleanup()

    @staticmethod
    def events():
        return [InputEvent(0, "key", ("ctrlleft", True)),
                InputEvent(.1, "button", (10, 20, "left", True)),
                InputEvent(.2, "move", (40, 50)),
                InputEvent(.3, "button", (40, 50, "left", False)),
                InputEvent(.4, "key", ("ctrlleft", False)),
                InputEvent(.5, "scroll", (40, 50, -2))]

    def test_drag_and_modifier_event_order(self):
        drafts = events_to_drafts(self.events())
        self.assertEqual([d.type_id for d in drafts],
                         ["按下键盘", "鼠标点击", "鼠标拖拽", "鼠标点击", "按下键盘", "滚轮滑动"])
        self.assertEqual([d.parameters["录制时间"] for d in drafts], [0, .1, .2, .3, .4, .5])
        self.assertTrue(drafts[2].parameters["录制保持按下"])
        self.assertEqual(len({d.parameters["录制批次"] for d in drafts}), 1)

    def test_stopping_with_inputs_held_adds_release_commands(self):
        drafts = events_to_drafts(self.events()[:3])
        self.assertEqual([d.parameters.get("录制动作") for d in drafts[-2:]], ["松开", "松开"])

    def test_unmatched_releases_and_empty_recording(self):
        self.assertEqual(events_to_drafts([]), [])
        self.assertEqual(events_to_drafts([InputEvent(0, "key", ("a", False))]), [])

    def test_timing_can_be_disabled(self):
        drafts = events_to_drafts(self.events(), False)
        self.assertTrue(all(d.parameters["录制时间"] == 0 for d in drafts))

    def test_bounded_and_sampled_buffer_only_records_while_active(self):
        clock = [0]
        buffer = RecordingBuffer(limit=2, clock=lambda: clock[0])
        buffer.append("move", 1, 1)
        self.assertEqual(buffer.snapshot(), ())
        buffer.start()
        buffer.append("move", 1, 1)
        clock[0] = .01
        buffer.append("move", 2, 2)
        clock[0] = .1
        buffer.append("move", 3, 3)
        buffer.append("key", "a", True)
        self.assertEqual(len(buffer.snapshot()), 2)
        self.assertTrue(buffer.full)
        self.assertFalse(buffer.active)

    def test_append_keeps_existing_graph_and_exports_recording(self):
        existing = self.repository.add_command(InstructionDraft("时间等待", {"时长": 0, "单位": "秒"}))
        old_edges = self.repository.snapshot().edges
        ids = self.repository.append_recording(events_to_drafts(self.events()))
        snapshot = self.repository.execution_snapshot()
        self.assertEqual(len(snapshot.commands), 7)
        self.assertEqual(snapshot.commands[0].id, existing.id)
        self.assertTrue(all(edge in snapshot.edges for edge in old_edges))
        self.assertEqual(len(ids), 6)
        workbook = Workbook()
        self.repository.export_to_workbook(workbook, self.database)
        reopened_db = DatabaseOperation(os.path.join(self.directory.name, "reopened.db"))
        reopened = GraphRepository(reopened_db.db_path)
        reopened.import_from_workbook(workbook)
        self.assertEqual([c.parameters for c in reopened.snapshot().commands],
                         [c.parameters for c in snapshot.commands])
        self.assertEqual(reopened.snapshot().edges, snapshot.edges)

    def test_bad_batch_is_atomic(self):
        with self.assertRaises(ValueError):
            self.repository.append_recording([InstructionDraft("时间等待", {}), InstructionDraft("不存在", {})])
        self.assertEqual(self.repository.list_commands(), [])

    def test_recording_editor_keeps_replay_metadata(self):
        for draft in events_to_drafts(self.events()):
            editor = get_instruction_spec(draft.type_id).create_editor(draft=draft)
            edited = editor.get_draft()
            for key, value in draft.parameters.items():
                if key.startswith("录制"):
                    self.assertEqual(edited.parameters[key], value)
            editor.close()

    def test_replay_balances_drag_and_keys_without_real_input(self):
        gui = Mock(FAILSAFE=True)
        context = ExecutionContext()
        with patch("instructions.common.actions.pyautogui_module", return_value=gui):
            for draft in events_to_drafts(self.events()):
                command = CommandRecord(1, draft.type_id, draft.parameters)
                get_instruction_spec(command.type_id).create_executor().execute(context, command)
            self.assertEqual(gui.keyDown.call_args.args, ("ctrlleft",))
            gui.mouseDown.assert_called_once_with(button="left", _pause=False)
            gui.mouseUp.assert_called_once_with(button="left", _pause=False)
            gui.dragTo.assert_not_called()
            self.assertEqual(context.metadata["recorded_keys"], set())
            self.assertEqual(context.metadata["recorded_buttons"], set())

    def test_interrupted_replay_releases_held_inputs_even_at_failsafe_corner(self):
        gui = Mock(FAILSAFE=True)
        context = ExecutionContext(metadata={"recorded_keys": {"shift"}, "recorded_buttons": {"right"}})
        with patch("instructions.common.actions.pyautogui_module", return_value=gui):
            release_recorded_inputs(context)
        gui.keyUp.assert_called_once_with("shift", _pause=False)
        gui.mouseUp.assert_called_once_with(button="right", _pause=False)
        self.assertTrue(gui.FAILSAFE)

    def test_windows_key_normalization(self):
        self.assertEqual(normalize_key(SimpleNamespace(vk=65, char="A"), "win32"), "a")
        self.assertEqual(normalize_key(SimpleNamespace(vk=49, char="!"), "win32"), "1")
        self.assertEqual(normalize_key(SimpleNamespace(name="ctrl_l")), "ctrlleft")

    def test_non_windows_native_keycodes_are_not_windows_virtual_keys(self):
        self.assertEqual(normalize_key(SimpleNamespace(vk=65, char=" "), "linux"), " ")
        self.assertEqual(normalize_key(SimpleNamespace(vk=49, char="n"), "darwin"), "n")
        self.assertEqual(normalize_key(SimpleNamespace(vk=10, char="!"), "linux"), "1")

    def test_sampling_preserves_final_position_and_position_before_key(self):
        now = [0]
        buffer = RecordingBuffer(clock=lambda: now[0])
        buffer.start()
        buffer.append("move", 10, 20)
        now[0] = .01
        buffer.append("move", 30, 40)
        self.assertEqual(buffer.stop()[-1].data, (30, 40))
        buffer.start()
        buffer.append("move", 10, 20)
        now[0] = .02
        buffer.append("move", 30, 40)
        buffer.append("key", "a", True)
        self.assertEqual([event.kind for event in buffer.snapshot()], ["move", "move", "key"])

    def test_ui_manual_write_updates_shared_table_flow_and_code_once(self):
        class Workspace(QObject):
            graphFinalized = Signal(bool)
            statusMessage = Signal(str)
        window = QMainWindow()
        workspace = Workspace()
        workspace.repository = self.repository
        workspace.reload_graph = Mock()
        window.workspace = workspace
        window.command_thread = SimpleNamespace(isRunning=lambda: False)
        view = ViewWorkspace.__new__(ViewWorkspace)
        view.window = SimpleNamespace(db=self.database, workspace=workspace)
        view.command_table, view.table_state = QTableWidget(0, 7), QLabel()
        view.code_editor, view.code_status = QPlainTextEdit(), QLabel()
        view._loading_code = view._code_dirty = False
        workspace.graphFinalized.connect(lambda _: view.refresh_table())
        workspace.graphFinalized.connect(lambda _: view._sync_code_if_needed(force=True))
        recorder_view = RecordingView(window)
        recorder_view.drafts = events_to_drafts(self.events())
        with patch("recording_view.QMessageBox.warning", side_effect=AssertionError("unexpected write error")):
            recorder_view.write()
            recorder_view.write()
        self.assertEqual(view.command_table.rowCount(), 6)
        self.assertIn("鼠标拖拽", view.code_editor.toPlainText())
        self.assertEqual(len(self.repository.snapshot().nodes), 8)
        self.repository.validate_graph()
        recorder_view.shutdown()
        window.close()

    def test_countdown_cancel_does_not_install_listener(self):
        window = QMainWindow()
        window.command_thread = SimpleNamespace(isRunning=lambda: False)
        widget = RecordingView(window)
        with patch("recording_view.GlobalInputRecorder") as backend:
            widget.begin()
            self.assertTrue(widget.busy)
            widget.finish()
            backend.assert_not_called()
        self.assertFalse(widget.busy)
        window.close()

    def test_listener_stop_removes_only_own_listeners(self):
        listener = Mock()
        buffer = RecordingBuffer()
        recorder = GlobalInputRecorder(buffer, Mock(), Mock())
        recorder.listeners = [listener]
        recorder.stop()
        listener.stop.assert_called_once()
        listener.join.assert_called_once_with(timeout=.5)
        self.assertEqual(recorder.listeners, [])

    def test_global_callback_f8_stops_without_recording_it(self):
        listeners = []
        class Listener:
            def __init__(self, **callbacks):
                self.callbacks = callbacks
                listeners.append(self)
            def start(self): pass
            def stop(self): pass
            def join(self, timeout): pass
        buffer = RecordingBuffer()
        buffer.start()
        stopped = Mock()
        recorder = GlobalInputRecorder(buffer, stopped, Mock())
        pynput = SimpleNamespace(keyboard=SimpleNamespace(Listener=Listener), mouse=SimpleNamespace(Listener=Listener))
        with patch.dict("sys.modules", {"pynput": pynput, "pyautogui": SimpleNamespace(KEYBOARD_KEYS=["a", "f8"])}):
            recorder.start()
            listeners[0].callbacks["on_press"](SimpleNamespace(vk=65, char="a"))
            listeners[0].callbacks["on_release"](SimpleNamespace(vk=65, char="a"))
            listeners[0].callbacks["on_press"](SimpleNamespace(name="f8"))
        stopped.assert_called_once()
        self.assertEqual([event.data for event in buffer.snapshot()], [("a", True), ("a", False)])
        recorder.stop()
        # A stale listener callback must not contaminate a later recording.
        buffer.start()
        self.assertFalse(listeners[0].callbacks["on_press"](SimpleNamespace(vk=65, char="a")))
        self.assertEqual(buffer.snapshot(), ())

    def test_recorded_deadline_wait_is_interruptible_and_does_not_drift(self):
        with patch("main_work.DatabaseOperation", return_value=self.database):
            thread = CommandThread(SimpleNamespace(execution_services={}))
        thread.start_state = True
        context = ExecutionContext()
        now = [100.0]
        executor = Mock()
        spec = SimpleNamespace(display_name="录制", create_executor=lambda: executor)
        command = CommandRecord(1, "按下键盘", {"录制批次": "test", "录制时间": .2, "按键": "a"})
        with patch("main_work.time.monotonic", side_effect=lambda: now[0]), \
             patch("main_work.time.sleep", side_effect=lambda duration: now.__setitem__(0, now[0] + duration)), \
             patch("main_work.get_instruction_spec", return_value=spec):
            thread._execute_one(command, context)
        executor.execute.assert_called_once()
        self.assertAlmostEqual(now[0], 100.2)
        executor.reset_mock()
        command.parameters["录制时间"] = 10
        with patch("main_work.time.monotonic", side_effect=lambda: now[0]), \
             patch("main_work.time.sleep", side_effect=lambda duration: setattr(thread, "start_state", False)), \
             patch("main_work.get_instruction_spec", return_value=spec):
            thread._execute_one(command, context)
        executor.execute.assert_not_called()
