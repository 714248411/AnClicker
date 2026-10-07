import os
os.environ.setdefault("QT_QPA_PLATFORM", "offscreen")
import tempfile
import unittest
from PySide6.QtCore import QPointF, Qt
from PySide6.QtGui import QColor
from PySide6.QtTest import QSignalSpy
from PySide6.QtWidgets import QApplication
from node_editor.items import NodeItem, EdgeItem
from node_editor.scene import NodeScene
from instruction_workspace import InstructionWorkspace
from instructions.models import InstructionDraft
from 数据库操作 import DatabaseOperation


class ConditionPortTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.app = QApplication.instance() or QApplication([])

    def node(self):
        return NodeItem("condition", 1, "条件判断", "条件判断", QColor("#5b6fdc"), control_kind_="condition")

    def test_three_ports_and_quarter_regions(self):
        node = self.node()
        def port(x, y):
            return node.connection_port_at(QPointF(x * node.width, y * node.height))
        self.assertIs(port(.5, .2), node.no_port)
        self.assertIs(port(.2, .5), node.input_port)
        self.assertIs(port(.8, .5), node.output_port)
        self.assertIsNone(port(.5, .5))
        self.assertIs(port(.1, .2), node.input_port)
        self.assertIs(port(.2, .1), node.no_port)
        self.assertIs(port(.9, .2), node.output_port)
        self.assertIs(port(.8, .1), node.no_port)
        self.assertIs(port(.2, .2), node.no_port)
        self.assertEqual(node.no_port.link_kind, 2)
        self.assertEqual(node.output_port.link_kind, 1)

    def test_top_drag_requests_false_even_when_drawn_first(self):
        scene = NodeScene()
        source = self.node()
        target = NodeItem("target", 2, "时间等待", "目标", QColor("#5b6fdc"))
        for node in (source, target):
            scene.addItem(node)
            scene.nodes_by_id[node.node_id] = node
        target.setPos(300, 100)
        spy = QSignalSpy(scene.branchConnectionRequested)
        scene.begin_port_connection(source.no_port)
        scene.end_port_connection(target.mapToScene(QPointF(target.width / 2, target.height / 2)))
        self.assertEqual(spy.at(0), ["condition", "target", 2])
        scene.begin_port_connection(source.output_port)
        scene.end_port_connection(target.mapToScene(QPointF(target.width / 2, target.height / 2)))
        self.assertEqual(spy.at(1), ["condition", "target", 1])

    def test_false_edge_attaches_to_top_and_moves_with_node(self):
        scene = NodeScene()
        source = self.node()
        target = NodeItem("target", 2, "时间等待", "目标", QColor("#5b6fdc"))
        scene.addItem(source)
        scene.addItem(target)
        target.setPos(400, 0)
        edge = EdgeItem(source, target, 2)
        scene.addItem(edge)
        self.assertIs(edge.source_port, source.no_port)
        self.assertEqual(edge.path().pointAtPercent(0), source.no_port.scenePos())
        source.setPos(20, 30)
        self.assertEqual(edge.path().pointAtPercent(0), source.no_port.scenePos())

    def test_hotspot_mouse_press_starts_single_port(self):
        scene = NodeScene()
        node = self.node()
        scene.addItem(node)
        class Event:
            def button(self): return Qt.MouseButton.LeftButton
            def pos(self): return QPointF(node.width / 2, node.height * .2)
            def accept(self): pass
        node.mousePressEvent(Event())
        self.assertIs(scene._connection_port, node.no_port)
        scene.cancel_port_connection()

    def test_workspace_persists_false_before_true_and_reload_uses_top(self):
        with tempfile.TemporaryDirectory() as directory:
            database = DatabaseOperation(os.path.join(directory, "ports.db"))
            workspace = InstructionWorkspace(database.db_path)
            repo = workspace.repository
            condition = repo.add_command(InstructionDraft("条件判断", {"条件": "True"}), unconnected=True)
            no = repo.add_command(InstructionDraft("时间等待", {"时长": 0}), unconnected=True)
            yes = repo.add_command(InstructionDraft("时间等待", {"时长": 0}), unconnected=True)
            workspace.reload_graph()
            nodes = {node.command_id: node.node_id for node in repo.snapshot().nodes if node.command_id}
            workspace._connect_nodes(nodes[condition.id], nodes[no.id], 2)
            workspace._connect_nodes(nodes[condition.id], nodes[yes.id], 1)
            kinds = {edge.target: edge.kind for edge in repo.snapshot().edges}
            self.assertEqual(kinds[nodes[no.id]], 2)
            self.assertEqual(kinds[nodes[yes.id]], 1)
            edge = next(edge for edge in workspace.editor.scene.edges if edge.link_kind == 2)
            self.assertIs(edge.source_port, edge.source_node.no_port)
            workspace.editor.close()
            workspace.palette.close()
