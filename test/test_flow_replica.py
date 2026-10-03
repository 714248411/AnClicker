import os
import tempfile
import unittest
from types import MethodType
from unittest.mock import patch

from graph_repository import END_NODE_ID, START_NODE_ID, GraphRepository
from instructions.models import ExecutionContext, InstructionDraft
from main_work import CommandThread
from 数据库操作 import DatabaseOperation


class FlowReplicaTests(unittest.TestCase):
    def setUp(self):
        self.temporary_directory = tempfile.TemporaryDirectory()
        self.database_path = os.path.join(self.temporary_directory.name, "flow.db")
        self.database = DatabaseOperation(self.database_path)
        self.repository = GraphRepository(
            self.database_path, valid_type_ids={"循环", "时间等待"}
        )

    def tearDown(self):
        self.temporary_directory.cleanup()

    def _loop_graph(self):
        loop = self.repository.add_command(
            InstructionDraft("循环", {"方式": "次数", "条件": "True", "次数": 2}),
            unconnected=True,
        )
        body = self.repository.add_command(
            InstructionDraft("时间等待", {"时长": 0, "单位": "秒"}),
            unconnected=True,
        )
        nodes = {
            node.command_id: node.node_id
            for node in self.repository.snapshot().nodes
            if node.command_id is not None
        }
        self.repository.connect_nodes(START_NODE_ID, nodes[loop.id])
        self.repository.connect_nodes(nodes[loop.id], nodes[body.id])
        self.repository.connect_nodes(nodes[loop.id], END_NODE_ID)
        self.repository.connect_nodes(nodes[body.id], nodes[loop.id])
        return loop, body

    def test_loop_links_keep_body_and_completed_roles(self):
        loop, _body = self._loop_graph()
        snapshot = self.repository.validate_graph()
        loop_node = next(node for node in snapshot.nodes if node.command_id == loop.id)
        outgoing = {edge.kind for edge in snapshot.edges if edge.source == loop_node.node_id}
        self.assertEqual(outgoing, {3, 4})

    def test_count_loop_traverses_body_exactly_requested_times(self):
        loop, body = self._loop_graph()

        class MainWindowStub:
            execution_services = {}

        with patch("main_work.DatabaseOperation", return_value=self.database):
            thread = CommandThread(MainWindowStub())
        executed = []

        def execute_one(_self, command, _context):
            executed.append(command.id)
            return True

        thread._execute_one = MethodType(execute_one, thread)
        thread._persist_variables = lambda _variables: None
        thread.start_state = True
        thread._execute_flow(
            self.repository.validate_graph(), ExecutionContext(variables={})
        )
        self.assertEqual(executed, [loop.id, body.id, loop.id, body.id, loop.id])


if __name__ == "__main__":
    unittest.main()
