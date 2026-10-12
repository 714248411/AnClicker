import os
import tempfile
import unittest
from types import SimpleNamespace

os.environ.setdefault("QT_QPA_PLATFORM", "offscreen")

from qt_compat.QtGui import QColor, QPainterPathStroker
from qt_compat.QtWidgets import QApplication, QLabel, QPlainTextEdit, QTableWidget

from graph_repository import END_NODE_ID, START_NODE_ID, GraphRepository
from instructions.models import InstructionDraft
from node_editor.items import EdgeItem, NodeItem
from node_editor.scene import NodeScene
from view_workspace import ViewWorkspace
from 数据库操作 import DatabaseOperation


class ViewLinkageTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.app = QApplication.instance() or QApplication([])

    def setUp(self):
        self.directory = tempfile.TemporaryDirectory()
        self.database = DatabaseOperation(os.path.join(self.directory.name, "linkage.db"))
        self.repository = GraphRepository(self.database.db_path)
        self.view = ViewWorkspace.__new__(ViewWorkspace)
        self.view.window = SimpleNamespace(
            db=self.database,
            workspace=SimpleNamespace(repository=self.repository),
        )
        self.view.command_table = QTableWidget(0, 7)
        self.view.table_state = QLabel()
        self.view.code_editor = QPlainTextEdit()
        self.view.code_status = QLabel()
        self.view._loading_code = False
        self.view._code_dirty = False
        self.view.running_command_id = None

    def tearDown(self):
        self.directory.cleanup()

    @staticmethod
    def draft(note="联动测试"):
        return InstructionDraft(
            "时间等待",
            {"类型": "时间等待", "时长": 2, "单位": "秒"},
            repeat_count=3,
            error_policy="自动跳过",
            note=note,
        )

    def test_draft_and_complete_flow_project_to_table_and_code(self):
        command = self.repository.add_command(self.draft(), unconnected=True)
        self.view.refresh_table()
        self.assertEqual(self.view.command_table.rowCount(), 1)
        self.assertIn("流程草稿", self.view.table_state.text())
        self.assertEqual(self.view.command_table.item(0, 1).text(), f"#{command.id}")
        self.assertEqual(self.view.command_table.item(0, 2).text(), "时间等待")
        self.assertIn('"时长": 2', self.view.command_table.item(0, 3).text())
        self.assertEqual(self.view.command_table.item(0, 4).text(), "3")

        self.assertTrue(self.view._sync_code_if_needed(force=True))
        draft_code = self.view.code_editor.toPlainText()
        self.assertIn("状态：流程草稿", draft_code)
        self.assertIn(f"#{command.id} 时间等待", draft_code)

        node = next(
            node for node in self.repository.snapshot().nodes
            if node.command_id == command.id
        )
        self.assertFalse(self.repository.connect_nodes(START_NODE_ID, node.node_id))
        self.assertTrue(self.repository.connect_nodes(node.node_id, END_NODE_ID))
        self.view.refresh_table()
        self.assertIn("已同步", self.view.table_state.text())
        self.assertTrue(self.view._sync_code_if_needed(force=True))
        self.assertIn("状态：流程完整，可执行", self.view.code_editor.toPlainText())

    def test_manual_code_survives_until_the_flow_changes(self):
        command = self.repository.add_command(self.draft())
        self.view._sync_code_if_needed(force=True)
        signature = self.database.get_setting_value("多功能流程签名")
        self.database.set_setting_value("多功能代码", "# 用户代码\n")
        self.database.set_setting_value("多功能流程签名", signature)

        self.view._load_code()
        self.assertEqual(self.view.code_editor.toPlainText(), "# 用户代码\n")

        self.repository.update_command_note(command.id, "备注已变化")
        self.view._load_code()
        self.assertIn("备注已变化", self.view.code_editor.toPlainText())
        self.assertNotEqual(self.view.code_editor.toPlainText(), "# 用户代码\n")

    def test_condition_branches_have_the_same_roles_in_table_and_code(self):
        condition = self.repository.add_command(
            InstructionDraft(
                "条件判断", {"条件": "状态 == '完成'"}, note="分支入口"
            ),
            unconnected=True,
        )
        yes_command = self.repository.add_command(self.draft("是分支"), unconnected=True)
        no_command = self.repository.add_command(self.draft("否分支"), unconnected=True)
        nodes = {
            node.command_id: node.node_id
            for node in self.repository.snapshot().nodes
            if node.command_id is not None
        }
        self.repository.connect_nodes(START_NODE_ID, nodes[condition.id])
        self.repository.connect_nodes(nodes[condition.id], nodes[yes_command.id], kind=1)
        self.repository.connect_nodes(nodes[condition.id], nodes[no_command.id], kind=2)
        self.repository.connect_nodes(nodes[yes_command.id], END_NODE_ID)
        self.assertTrue(self.repository.connect_nodes(nodes[no_command.id], END_NODE_ID))

        self.view.refresh_table()
        self.view._sync_code_if_needed(force=True)
        code = self.view.code_editor.toPlainText()
        self.assertEqual(self.view.command_table.rowCount(), 3)
        self.assertEqual(self.view.command_table.item(0, 2).text(), "条件判断")
        self.assertIn("状态 == '完成'", self.view.command_table.item(0, 3).text())
        self.assertIn("--是-->", code)
        self.assertIn("--否-->", code)

    def test_edge_routing_avoids_a_node_between_endpoints(self):
        scene = NodeScene()
        color = QColor("#7c8cff")
        source = NodeItem("source", 1, "时间等待", "源", color)
        obstacle = NodeItem("obstacle", 2, "时间等待", "中间节点", color)
        target = NodeItem("target", 3, "时间等待", "目标", color)
        for node, x, y in (
            (source, 0.0, 100.0),
            (obstacle, 210.0, 100.0),
            (target, 440.0, 100.0),
        ):
            scene.addItem(node)
            node.setPos(x, y)
            scene.nodes_by_id[node.node_id] = node
        edge = EdgeItem(source, target)
        scene.addItem(edge)
        scene.edges.append(edge)
        scene.reroute_edges()

        stroker = QPainterPathStroker()
        stroker.setWidth(4.0)
        routed_shape = stroker.createStroke(edge.path())
        self.assertFalse(
            routed_shape.intersects(
                obstacle.sceneBoundingRect().adjusted(-8.0, -8.0, 8.0, 8.0)
            )
        )


if __name__ == "__main__":
    unittest.main()
