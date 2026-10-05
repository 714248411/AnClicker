"""Insertion-order fallback and incomplete linked graph runtime regressions."""
import os
import tempfile
import sqlite3
from contextlib import closing
import unittest
from unittest.mock import patch

from graph_repository import GraphRepository, GraphValidationError
from instructions.models import ExecutionContext, InstructionDraft
from main_work import CommandThread
from 数据库操作 import DatabaseOperation


class ExecutionOrderTests(unittest.TestCase):
    def setUp(self):
        self.temp = tempfile.TemporaryDirectory()
        self.db = DatabaseOperation(os.path.join(self.temp.name, "run.db"))
        self.repo = GraphRepository(self.db.db_path)

    def tearDown(self):
        self.temp.cleanup()

    def add(self):
        return self.repo.add_command(InstructionDraft(
            "时间等待", {"时长": 0, "单位": "秒"}), unconnected=True).id

    def node(self, command_id):
        return next(n.node_id for n in self.repo.snapshot().nodes
                    if n.command_id == command_id)

    def run_ids(self, stop_after=None):
        with patch("main_work.DatabaseOperation", return_value=self.db):
            thread = CommandThread(type("Window", (), {"execution_services": {}})())
        thread.repository = self.repo
        thread.run_mode = ("全部指令", None)
        thread.start_state = True
        result = []
        def execute(command, context):
            result.append(command.id)
            if stop_after and len(result) == stop_after:
                context.stop_requested = True
            return True
        thread._execute_one = execute
        thread._persist_variables = lambda variables: None
        thread._execute_commands(thread._commands_for_mode(), ExecutionContext(variables={}))
        return result

    def test_no_edges_uses_insertion_order(self):
        ids = [self.add() for _ in range(3)]
        self.assertEqual(self.run_ids(), ids)

    def test_linked_chain_first_then_remaining_insertion_order(self):
        a, b, c, d = [self.add() for _ in range(4)]
        self.repo.connect_nodes(self.node(c), self.node(b))
        self.assertEqual(self.run_ids(), [c, b, a, d])

    def test_start_chain_can_end_without_end_node(self):
        a, b, c = [self.add() for _ in range(3)]
        self.repo.connect_nodes("start", self.node(c))
        self.repo.connect_nodes(self.node(c), self.node(a))
        self.assertEqual(self.run_ids(), [c, a, b])

    def test_shared_tail_runs_once(self):
        a, b, c = [self.add() for _ in range(3)]
        self.repo.connect_nodes(self.node(a), self.node(c))
        self.repo.connect_nodes(self.node(b), self.node(c))
        self.assertEqual(self.run_ids(), [a, c, b])

    def test_deleted_draft_normalizes_order(self):
        a, b, c = [self.add() for _ in range(3)]
        self.repo.delete_commands([b], preserve_flow=False)
        self.assertEqual([item.order for item in self.repo.list_commands()], [0, 1])
        self.assertEqual(self.run_ids(), [a, c])

    def test_each_repeat_starts_with_fresh_execution_tracking(self):
        ids = [self.add() for _ in range(2)]
        self.assertEqual(self.run_ids(), ids)
        self.assertEqual(self.run_ids(), ids)

    def test_stop_prevents_remaining_commands(self):
        ids = [self.add() for _ in range(3)]
        self.assertEqual(self.run_ids(stop_after=1), ids[:1])

    def test_old_order_gaps_do_not_prevent_run_and_reopen_repairs_them(self):
        ids = [self.add() for _ in range(3)]
        with closing(sqlite3.connect(self.db.db_path)) as connection:
            with connection:
                connection.execute("UPDATE 命令 SET 排序=排序+10")
        self.assertEqual(self.run_ids(), ids)
        DatabaseOperation(self.db.db_path)
        self.assertEqual([item.order for item in self.repo.list_commands()], [0, 1, 2])

    def test_uncontrolled_cycle_rejected_before_execution(self):
        a, b = [self.add() for _ in range(2)]
        self.repo.connect_nodes(self.node(a), self.node(b))
        self.repo.connect_nodes(self.node(b), self.node(a))
        with self.assertRaises(GraphValidationError):
            self.run_ids()

    def test_unselected_branch_is_fallback_after_earlier_unconnected_command(self):
        a = self.add()
        condition = self.repo.add_command(InstructionDraft(
            "条件判断", {"条件": "True"}), unconnected=True).id
        yes, no = self.add(), self.add()
        self.repo.connect_nodes("start", self.node(condition))
        self.repo.connect_nodes(self.node(condition), self.node(yes))
        self.repo.connect_nodes(self.node(condition), self.node(no))
        self.assertEqual(self.run_ids(), [condition, yes, a, no])
