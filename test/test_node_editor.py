import os
import unittest
from dataclasses import dataclass

os.environ.setdefault("QT_QPA_PLATFORM", "offscreen")

from PySide6.QtCore import QMimeData, QPointF, Qt
from PySide6.QtGui import QDropEvent, QKeyEvent
from PySide6.QtWidgets import QApplication

from node_editor import INSTRUCTION_MIME_TYPE, InstructionPalette, NodeEditorWidget
from node_editor.palette import TYPE_ID_ROLE


SPECS = {
    "image_click": {
        "title": "图像点击",
        "category": "键鼠指令",
        "color": "#1f6feb",
    },
    "time_wait": {
        "title": "时间等待",
        "category": "等待",
        "color": "#9e6a03",
    },
}


class NodeEditorTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.app_ = QApplication.instance() or QApplication([])

    def make_editor(self):
        editor_ = NodeEditorWidget()
        nodes_ = [
            {"id": 1, "command_id": 1, "type_id": "image_click", "x": 0, "y": 70},
            {"id": 2, "command_id": 2, "type_id": "time_wait", "x": 0, "y": 140},
        ]
        editor_.load_graph(nodes_, [], SPECS)
        return editor_

    def test_palette_is_searchable_and_only_instructions_are_draggable(self):
        palette_ = InstructionPalette(SPECS)
        self.assertEqual(palette_.tree.topLevelItemCount(), 2)
        first_category_ = palette_.tree.topLevelItem(0)
        first_instruction_ = first_category_.child(0)
        self.assertFalse(first_category_.flags() & Qt.ItemFlag.ItemIsDragEnabled)
        self.assertTrue(first_instruction_.flags() & Qt.ItemFlag.ItemIsDragEnabled)
        self.assertEqual(first_instruction_.data(0, TYPE_ID_ROLE), "image_click")
        palette_.tree.setCurrentItem(first_instruction_)
        self.assertEqual(palette_.selected_type_id(), "image_click")
        palette_.tree.setCurrentItem(first_category_)
        self.assertIsNone(palette_.selected_type_id())

        activated_: list[str] = []
        double_clicked_: list[str] = []
        palette_.instructionActivated.connect(activated_.append)
        palette_.instructionDoubleClicked.connect(double_clicked_.append)
        palette_.tree._activate_item(first_instruction_, 0)
        self.assertEqual(activated_, ["image_click"])
        self.assertEqual(double_clicked_, ["image_click"])

        palette_.search_edit.setText("时间")
        self.assertTrue(first_category_.isHidden())
        wait_category_ = palette_.tree.topLevelItem(1)
        self.assertFalse(wait_category_.isHidden())
        self.assertFalse(wait_category_.child(0).isHidden())

    def test_palette_accepts_registry_style_dataclass_specs(self):
        @dataclass(frozen=True)
        class RegistrySpec:
            type_id: str
            display_name: str
            category: str
            node_color: str

        palette_ = InstructionPalette(
            [RegistrySpec("图像点击", "图像点击", "键鼠", "#123456")]
        )
        item_ = palette_.tree.topLevelItem(0).child(0)
        self.assertEqual(item_.data(0, TYPE_ID_ROLE), "图像点击")
        self.assertEqual(palette_.specs()["图像点击"].color.name(), "#123456")

    def test_load_graph_adds_fixed_terminals_and_uses_one_flow_chain(self):
        editor_ = self.make_editor()
        scene_ = editor_.scene
        self.assertEqual(len(scene_.nodes_by_id), 4)
        self.assertEqual(len(scene_.edges), 3)
        self.assertEqual(
            [node_.command_id for node_ in scene_.chain_order if not node_.is_terminal],
            [1, 2],
        )

        start_node_ = scene_.nodes_by_id[scene_.START_NODE_ID]
        end_node_ = scene_.nodes_by_id[scene_.END_NODE_ID]
        self.assertTrue(start_node_.is_terminal)
        self.assertIsNone(start_node_.input_port)
        self.assertIsNotNone(start_node_.output_port)
        self.assertTrue(end_node_.is_terminal)
        self.assertIsNotNone(end_node_.input_port)
        self.assertIsNone(end_node_.output_port)
        for command_node_ in scene_.nodes_by_command_id.values():
            self.assertIsNotNone(command_node_.input_port)
            self.assertIsNotNone(command_node_.output_port)

    def test_explicit_invalid_graphs_are_rejected(self):
        nodes_ = [
            {"id": "s", "type_id": "start", "role": "start"},
            {"id": 1, "type_id": "image_click"},
            {"id": 2, "type_id": "time_wait"},
            {"id": "e", "type_id": "end", "role": "end"},
        ]
        fan_out_edges_ = [("s", 1), ("s", 2), (1, "e")]
        editor_ = NodeEditorWidget()
        with self.assertRaisesRegex(ValueError, "fan-out"):
            editor_.load_graph(nodes_, fan_out_edges_, SPECS)

        disconnected_edges_ = [("s", 1), (1, "e"), (2, "e")]
        with self.assertRaisesRegex(ValueError, "multiple inputs"):
            editor_.load_graph(nodes_, disconnected_edges_, SPECS)

    def test_focus_selection_activation_and_host_owned_delete_copy(self):
        editor_ = self.make_editor()
        self.assertTrue(editor_.focus_command(2))
        self.assertEqual(editor_.selected_command_ids(), [2])
        self.assertFalse(editor_.focus_command(999))

        activated_: list[int] = []
        copied_: list[list[int]] = []
        deleted_: list[list[int]] = []
        editor_.commandActivated.connect(activated_.append)
        editor_.copyRequested.connect(copied_.append)
        editor_.deleteRequested.connect(deleted_.append)
        editor_.scene.activate_node(editor_.scene.nodes_by_command_id[2])

        copy_event_ = QKeyEvent(
            QKeyEvent.Type.KeyPress,
            Qt.Key.Key_C,
            Qt.KeyboardModifier.ControlModifier,
        )
        editor_.view.keyPressEvent(copy_event_)
        delete_event_ = QKeyEvent(
            QKeyEvent.Type.KeyPress,
            Qt.Key.Key_Delete,
            Qt.KeyboardModifier.NoModifier,
        )
        editor_.view.keyPressEvent(delete_event_)
        self.assertEqual(activated_, [2])
        self.assertEqual(copied_, [[2]])
        self.assertEqual(deleted_, [[2]])
        self.assertIn(2, editor_.scene.nodes_by_command_id)

        editor_.scene.clearSelection()
        editor_.scene.nodes_by_id[editor_.scene.START_NODE_ID].setSelected(True)
        editor_.view.keyPressEvent(delete_event_)
        self.assertEqual(deleted_, [[2]])

    def test_palette_drop_is_reported_without_creating_an_unconfigured_node(self):
        editor_ = self.make_editor()
        editor_.resize(700, 500)
        editor_.show()
        self.app_.processEvents()
        dropped_: list[tuple[str, float, float]] = []
        editor_.instructionDropped.connect(
            lambda type_id_, x_, y_: dropped_.append((type_id_, x_, y_))
        )
        mime_data_ = QMimeData()
        mime_data_.setData(INSTRUCTION_MIME_TYPE, b"image_click")
        drop_event_ = QDropEvent(
            QPointF(100.0, 120.0),
            Qt.DropAction.CopyAction,
            mime_data_,
            Qt.MouseButton.LeftButton,
            Qt.KeyboardModifier.NoModifier,
        )
        previous_node_count_ = len(editor_.scene.nodes_by_id)
        editor_.view.dropEvent(drop_event_)
        self.assertEqual(len(dropped_), 1)
        self.assertEqual(dropped_[0][0], "image_click")
        self.assertEqual(len(editor_.scene.nodes_by_id), previous_node_count_)
        editor_.close()

    def test_drag_reorder_previews_before_release_and_commits_on_release(self):
        editor_ = self.make_editor()
        scene_ = editor_.scene
        node_2_ = scene_.nodes_by_command_id[2]
        previews_: list[list[int]] = []
        commits_: list[list[int]] = []
        graph_commits_: list[tuple[list[int], object, float, float]] = []
        positions_: list[tuple[object, float, float]] = []
        editor_.reorderPreview.connect(previews_.append)
        editor_.reorderCommitted.connect(commits_.append)
        editor_.graphCommitted.connect(
            lambda order_, node_id_, x_, y_: graph_commits_.append(
                (order_, node_id_, x_, y_)
            )
        )
        editor_.positionCommitted.connect(
            lambda node_id_, x_, y_: positions_.append((node_id_, x_, y_))
        )

        scene_.begin_node_drag(node_2_)
        node_2_.setPos(0.0, 35.0)
        self.assertEqual(previews_[-1], [2, 1])
        self.assertEqual(commits_, [])
        scene_.end_node_drag(node_2_)
        self.assertEqual(commits_, [[2, 1]])
        self.assertEqual(graph_commits_, [([2, 1], 2, 0.0, 35.0)])
        self.assertEqual(scene_._command_order(scene_.chain_order), [2, 1])
        self.assertEqual(positions_, [])

    def test_free_move_without_insertion_keeps_order_and_commits_position(self):
        editor_ = self.make_editor()
        scene_ = editor_.scene
        node_1_ = scene_.nodes_by_command_id[1]
        commits_: list[list[int]] = []
        positions_: list[tuple[object, float, float]] = []
        editor_.reorderCommitted.connect(commits_.append)
        editor_.positionCommitted.connect(
            lambda node_id_, x_, y_: positions_.append((node_id_, x_, y_))
        )

        scene_.begin_node_drag(node_1_)
        node_1_.setPos(500.0, 500.0)
        scene_.end_node_drag(node_1_)
        self.assertEqual(node_1_.pos(), QPointF(500.0, 500.0))
        self.assertEqual(scene_._command_order(scene_.chain_order), [1, 2])
        self.assertEqual(commits_, [])
        self.assertEqual(positions_, [(1, 500.0, 500.0)])

    def test_terminal_can_move_but_is_never_a_command(self):
        editor_ = self.make_editor()
        scene_ = editor_.scene
        start_node_ = scene_.nodes_by_id[scene_.START_NODE_ID]
        committed_: list[tuple[object, float, float]] = []
        editor_.positionCommitted.connect(
            lambda node_id_, x_, y_: committed_.append((node_id_, x_, y_))
        )
        scene_.begin_node_drag(start_node_)
        start_node_.setPos(20.0, -80.0)
        scene_.end_node_drag(start_node_)
        self.assertEqual(committed_, [(scene_.START_NODE_ID, 20.0, -80.0)])
        start_node_.setSelected(True)
        self.assertNotIn(scene_.START_NODE_ID, editor_.selected_command_ids())


if __name__ == "__main__":
    unittest.main()
