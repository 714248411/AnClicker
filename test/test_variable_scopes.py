import os
os.environ.setdefault('QT_QPA_PLATFORM', 'offscreen')
import sqlite3
import tempfile
import unittest
from pathlib import Path
from unittest.mock import patch
from types import SimpleNamespace
from PySide6.QtWidgets import QApplication, QComboBox, QDialog
from 数据库操作 import DatabaseOperation
from instructions.models import ExecutionContext, CommandRecord
from instructions.registry import get_instruction_spec
from WindowControl.变量池窗口 import VariablePool_Win
from main_work import CommandThread


class VariableScopeTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.app = QApplication.instance() or QApplication([])

    def setUp(self):
        self.directory = tempfile.TemporaryDirectory()
        self.path = str(Path(self.directory.name)/'variables.db')
        self.db = DatabaseOperation(self.path)

    def tearDown(self):
        self.directory.cleanup()

    def test_legacy_migration_preserves_values_and_global_behavior(self):
        with sqlite3.connect(self.path) as connection:
            connection.execute('DROP TABLE 变量池')
            connection.execute('CREATE TABLE 变量池(变量名称 TEXT UNIQUE, 备注 TEXT, 值 TEXT)')
            connection.execute("INSERT INTO 变量池 VALUES('原变量','说明','42')")
        connection.close()
        migrated = DatabaseOperation(self.path)
        self.assertEqual(migrated.get_variable_definitions(), [('原变量','说明','42','全局变量')])
        self.assertEqual(migrated.get_value_from_variable_table(), [('原变量','说明','42')])

    def test_persistence_keeps_local_initial_values_and_rejects_duplicates_atomically(self):
        rows = [('共享','', '1','全局变量'), ('临时','', '2','普通变量')]
        self.db.save_variable_definitions(rows)
        with patch('main_work.DatabaseOperation', return_value=self.db):
            worker = CommandThread(SimpleNamespace(execution_services={}))
        current = worker._load_variables()
        current.update(共享='更新', 临时='本次值')
        worker._persist_variables(current)
        self.assertEqual(current['临时'], '本次值')
        self.assertEqual(worker._load_variables(), {'共享':'更新', '临时':'2'})
        before = self.db.get_variable_definitions()
        with self.assertRaises(ValueError):
            self.db.save_variable_definitions(rows+[rows[0]])
        self.assertEqual(self.db.get_variable_definitions(), before)

    def test_time_editor_selects_managed_variables_and_executor_writes_result(self):
        self.db.save_variable_definitions([('时间结果','','','普通变量')])
        context = ExecutionContext(variables=self.db.get_variable_info('dict'), metadata={'database':self.db})
        spec = get_instruction_spec('获取时间')
        editor = spec.create_editor(context=context)
        self.assertIsInstance(editor.ui.parameter_0, QComboBox)
        self.assertEqual(editor.ui.auxiliary_0.text(), '设置变量')
        editor.ui.parameter_0.setCurrentText('时间结果')
        draft = editor.get_draft()
        with patch('instructions.common.actions.current_time', return_value='2026-10-05 16:00:00'):
            spec.create_executor().execute(context, CommandRecord(1,draft.type_id,draft.parameters))
        self.assertEqual(context.variables['时间结果'], '2026-10-05 16:00:00')
        editor.close()

    def test_manager_can_add_both_scopes_and_cancel_without_saving(self):
        manager = VariablePool_Win(database=self.db)
        manager.add_row('普通变量')
        manager.add_row('全局变量')
        manager.save()
        self.assertEqual(manager.result(), QDialog.DialogCode.Accepted)
        self.assertEqual([row[3] for row in self.db.get_variable_definitions()], ['普通变量','全局变量'])
        reopened = VariablePool_Win(database=self.db)
        reopened.add_row()
        reopened.reject()
        self.assertEqual(len(self.db.get_variable_definitions()),2)
