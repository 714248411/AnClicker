import os
import tempfile
import threading
import unittest
from unittest.mock import MagicMock, patch

os.environ.setdefault("QT_QPA_PLATFORM", "offscreen")

from qt_compat.QtCore import Signal
from qt_compat.QtWidgets import QApplication, QDialog, QMainWindow, QMessageBox

from graph_repository import GraphRepository
from instruction_workspace import InstructionWorkspace
from instructions.models import InstructionDraft
from main_work import CommandThread
from 数据库操作 import DatabaseOperation


class _Editor(QDialog):
    test_requested = Signal(object)

    def __init__(self, draft_, accepted_=True, parent_=None):
        super().__init__(parent_)
        self._draft = draft_
        self._accepted = accepted_

    def exec(self):
        return (
            QDialog.DialogCode.Accepted
            if self._accepted
            else QDialog.DialogCode.Rejected
        )

    def get_draft(self):
        return self._draft


class _Spec:
    display_name = "时间等待"

    def __init__(self, draft_, accepted_=True):
        self._draft = draft_
        self._accepted = accepted_

    def create_editor(self, parent=None, draft=None, context=None):
        del draft, context
        return _Editor(self._draft, self._accepted, parent)


class RuntimeIntegrationTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.app = QApplication.instance() or QApplication([])

    def setUp(self):
        self.temporary_directory = tempfile.TemporaryDirectory()
        self.database = DatabaseOperation(
            os.path.join(self.temporary_directory.name, "runtime.db")
        )

    def tearDown(self):
        self.app.processEvents()
        self.temporary_directory.cleanup()

    @staticmethod
    def _draft(note_="", repeat_count_=1):
        return InstructionDraft(
            "时间等待",
            {"类型": "时间等待", "时长": 0, "单位": "秒"},
            repeat_count=repeat_count_,
            error_policy="自动跳过",
            note=note_,
        )

    def test_drop_cancel_creates_nothing_and_accept_creates_at_release_position(self):
        host_ = QMainWindow()
        host_.db = self.database
        workspace_ = InstructionWorkspace(self.database.db_path, host_)

        with patch(
            "instruction_workspace.get_instruction_spec",
            return_value=_Spec(self._draft(), accepted_=False),
        ):
            self.assertIsNone(workspace_.add_command("时间等待", 120.0, 0.0))
        self.assertEqual(workspace_.repository.list_commands(), [])

        with patch(
            "instruction_workspace.get_instruction_spec",
            return_value=_Spec(self._draft("已添加")),
        ):
            command_id_ = workspace_.add_command("时间等待", 120.0, 0.0)
        self.assertIsNotNone(command_id_)
        snapshot_ = workspace_.repository.snapshot()
        node_ = next(node_ for node_ in snapshot_.nodes if node_.command_id == command_id_)
        self.assertEqual((node_.x, node_.y), (120.0, 0.0))
        self.assertEqual([command_.note for command_ in snapshot_.commands], ["已添加"])
        self.assertTrue(workspace_.focus_command(command_id_))

    def test_edit_copy_delete_and_run_signals_use_stable_command_ids(self):
        repository_ = GraphRepository(self.database.db_path)
        original_ = repository_.add_command(self._draft("原始"))
        host_ = QMainWindow()
        host_.db = self.database
        workspace_ = InstructionWorkspace(self.database.db_path, host_)

        with patch(
            "instruction_workspace.get_instruction_spec",
            return_value=_Spec(self._draft("修改后")),
        ):
            self.assertTrue(workspace_.edit_command(original_.id))
        self.assertEqual(repository_.get_command(original_.id).note, "修改后")

        copied_ids_ = workspace_.copy_commands([original_.id])
        self.assertEqual(len(copied_ids_), 1)
        self.assertNotEqual(copied_ids_[0], original_.id)
        self.assertEqual(workspace_.remove_commands(copied_ids_, confirm=False), 1)

        single_ids_ = []
        from_ids_ = []
        workspace_.runSingleRequested.connect(single_ids_.append)
        workspace_.runFromRequested.connect(from_ids_.append)
        workspace_.run_from_command_single(original_.id)
        workspace_.run_from_command(original_.id)
        self.assertEqual(single_ids_, [original_.id])
        self.assertEqual(from_ids_, [original_.id])

    def test_workspace_drag_reorder_atomically_persists_order_and_position(self):
        repository_ = GraphRepository(self.database.db_path)
        first_ = repository_.add_command(self._draft("first"))
        second_ = repository_.add_command(self._draft("second"))
        host_ = QMainWindow()
        host_.db = self.database
        workspace_ = InstructionWorkspace(self.database.db_path, host_)
        scene_ = workspace_.editor.scene
        first_node_ = scene_.nodes_by_command_id[first_.id]
        original_order_ = list(scene_.chain_order)
        reordered_ = [
            original_order_[0],
            original_order_[2],
            original_order_[1],
            original_order_[3],
        ]

        scene_.begin_node_drag(first_node_)
        first_node_.setPos(321.0, 123.0)
        with patch.object(scene_, "_candidate_order", return_value=reordered_):
            scene_.end_node_drag(first_node_)

        snapshot_ = repository_.snapshot()
        self.assertEqual(
            [command_.id for command_ in snapshot_.commands],
            [second_.id, first_.id],
        )
        persisted_node_ = next(
            node_ for node_ in snapshot_.nodes if node_.command_id == first_.id
        )
        self.assertEqual((persisted_node_.x, persisted_node_.y), (321.0, 123.0))

    def test_command_thread_uses_registry_and_repeats_exactly_once_per_setting(self):
        repository_ = GraphRepository(self.database.db_path)
        first_ = repository_.add_command(self._draft("first", repeat_count_=3))
        second_ = repository_.add_command(self._draft("second", repeat_count_=2))
        executed_ids_ = []

        def execute_wait_(context, command):
            del context
            executed_ids_.append(command.id)

        class MainWindowStub:
            execution_services = {"时间等待": execute_wait_}

        with patch("main_work.DatabaseOperation", return_value=self.database):
            thread_ = CommandThread(MainWindowStub())
        thread_.set_repeat_number(1)
        thread_.set_run_mode("从当前行运行", second_.id)
        thread_.run()
        self.assertEqual(executed_ids_, [second_.id, second_.id])

        executed_ids_.clear()
        thread_.set_run_mode("单行指令", first_.id)
        thread_.run()
        self.assertEqual(executed_ids_, [first_.id, first_.id, first_.id])

    def test_paused_thread_can_stop_and_start_again_without_deadlock(self):
        repository_ = GraphRepository(self.database.db_path)
        repository_.add_command(self._draft("first"))
        repository_.add_command(self._draft("second"))
        first_entered_ = threading.Event()
        release_first_ = threading.Event()
        calls_: list[int] = []

        def execute_wait_(**kwargs_):
            command_ = kwargs_["command"]
            calls_.append(command_.id)
            if len(calls_) == 1:
                first_entered_.set()
                release_first_.wait(2)

        class MainWindowStub:
            execution_services = {"时间等待": execute_wait_}

        with patch("main_work.DatabaseOperation", return_value=self.database):
            thread_ = CommandThread(MainWindowStub())
        thread_.set_repeat_number(1)
        thread_.prepare_for_start()
        thread_.start()
        self.assertTrue(first_entered_.wait(2))
        thread_.pause()
        release_first_.set()
        self.assertTrue(thread_.stop_and_wait(2000))
        self.assertFalse(thread_.is_paused)

        calls_.clear()
        thread_.prepare_for_start()
        thread_.start()
        self.assertTrue(thread_.wait(2000))
        self.assertEqual(len(calls_), 2)

    def test_stop_uses_bounded_terminate_fallback_for_blocked_executor(self):
        class MainWindowStub:
            execution_services = {}

        with patch("main_work.DatabaseOperation", return_value=self.database):
            thread_ = CommandThread(MainWindowStub())
        with (
            patch.object(thread_, "isRunning", return_value=True),
            patch.object(thread_, "wait", side_effect=[False, True]) as wait_,
            patch.object(thread_, "terminate") as terminate_,
        ):
            self.assertTrue(thread_.stop_and_wait(25, 50))
        self.assertEqual(wait_.call_args_list[0].args, (25,))
        self.assertEqual(wait_.call_args_list[1].args, (50,))
        terminate_.assert_called_once_with()
        self.assertFalse(thread_.is_paused)

    def test_real_main_window_has_five_linked_views(self):
        class HotkeyStub:
            def register(self, *args_, **kwargs_):
                return None

            def unregister(self, *args_, **kwargs_):
                return None

        with (
            patch("Start_Win.DatabaseOperation", return_value=self.database),
            patch("main_work.DatabaseOperation", return_value=self.database),
            patch("Start_Win.SystemHotkey", HotkeyStub),
            patch("Start_Win.is_hotkey_valid", return_value=True),
        ):
            from Start_Win import Main_window

            window_ = Main_window()
        self.assertFalse(hasattr(window_, "tableWidget"))
        self.assertFalse(hasattr(window_, "groupBox_4"))
        self.assertEqual(len(window_.workspace.palette.specs()), 38)
        self.assertEqual(
            [
                window_.gridLayout_4.indexOf(window_.instructionPaletteHost),
                window_.gridLayout_4.indexOf(window_.tabWidget),
                window_.gridLayout_4.indexOf(window_.groupBox_3),
            ],
            [0, 1, 2],
        )
        window_.resize(1500, 900)
        window_.show()
        window_.view_workspace.show_flow()
        self.app.processEvents()
        self.assertEqual(
            [window_.tabWidget.tabText(index_) for index_ in range(5)],
            ["主界面", "表格", "流程图", "多功能", "导航"],
        )
        self.assertIs(
            window_.tabWidget.currentWidget(), window_.view_workspace.editor_page
        )
        self.assertTrue(window_.instructionPaletteHost.isVisible())
        window_.close()
        window_.deleteLater()

    def test_close_keeps_commands_when_required_save_is_cancelled(self):
        class HotkeyStub:
            def register(self, *args_, **kwargs_):
                return None

            def unregister(self, *args_, **kwargs_):
                return None

        repository_ = GraphRepository(self.database.db_path)
        repository_.add_command(self._draft("keep"))
        with (
            patch("Start_Win.DatabaseOperation", return_value=self.database),
            patch("main_work.DatabaseOperation", return_value=self.database),
            patch("Start_Win.SystemHotkey", HotkeyStub),
            patch("Start_Win.is_hotkey_valid", return_value=True),
        ):
            from Start_Win import Main_window

            window_ = Main_window()
        event_ = MagicMock()
        with (
            patch.object(self.database, "get_bool_setting", return_value=True),
            patch.object(window_, "save_data", return_value=False),
            patch("Start_Win.QMessageBox.question", return_value=QMessageBox.StandardButton.Yes),
        ):
            window_.closeEvent(event_)
        event_.ignore.assert_called_once()
        self.assertEqual(len(repository_.list_commands()), 1)
        window_.deleteLater()


if __name__ == "__main__":
    unittest.main()
