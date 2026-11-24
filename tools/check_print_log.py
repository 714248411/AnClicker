"""Print-log editing, repeated variable insertion and runtime output checks."""
import os
os.environ.setdefault('QT_QPA_PLATFORM', 'offscreen')
import sys
from pathlib import Path
sys.path.insert(0, str(Path(__file__).resolve().parents[1]))
import sqlite3
import tempfile
from types import SimpleNamespace
from anclicker.instructions.registry import get_instruction_spec, iter_instruction_specs
from anclicker.domain.instructions import InstructionDraft, CommandRecord, ExecutionContext
from anclicker.storage.graph_repository import GraphRepository
from anclicker.platform.qt_compat.QtWidgets import QApplication
from anclicker.platform.qt_compat.QtGui import QTextCursor

app = QApplication.instance() or QApplication([])
spec = get_instruction_spec('打印日志')
assert spec.category == '其他' and spec in list(iter_instruction_specs('其他'))
db_variables = {'数据库变量': 9, '数量': 2}
context = SimpleNamespace(variables={'数量': 1, '名称': '测试'}, metadata={
    'database': SimpleNamespace(get_variable_info=lambda _: db_variables),
    'condition_hint': lambda: {'target_variables': ['临时结果'], 'candidates': ['数量']}})
editor = spec.create_editor(context=context)
assert editor.content.toPlainText() == '', 'Loading the picker must not insert anything'
assert editor.variable_combo.findText('数据库变量') > 0
assert editor.variable_combo.findText('临时结果') > 0
editor.content.setPlainText('开始结束')
cursor = editor.content.textCursor(); cursor.setPosition(2); editor.content.setTextCursor(cursor)
for _ in range(2):
    index = editor.variable_combo.findText('数量')
    editor.variable_combo.setCurrentIndex(index)
    editor.variable_combo.activated[int].emit(index)
    assert editor.variable_combo.currentIndex() == 0
assert editor.content.toPlainText() == '开始{{数量}}{{数量}}结束'
# Selection replacement, keyboard caret and refresh do not insert extra placeholders.
cursor = editor.content.textCursor(); cursor.setPosition(0); cursor.setPosition(2, QTextCursor.KeepAnchor)
editor.content.setTextCursor(cursor)
editor.variable_combo.activated[int].emit(editor.variable_combo.findText('名称'))
assert editor.content.toPlainText() == '{{名称}}{{数量}}{{数量}}结束'
db_variables['新变量'] = 1
before = editor.content.toPlainText(); editor.refresh_button.click()
assert editor.content.toPlainText() == before and editor.variable_combo.findText('新变量') > 0
editor.content.setPlainText('名称={{名称}}\n数量={{数量}} / {{数量}}')
editor.repeat.setValue(2); editor.note.setText('日志测试')
draft = editor.get_draft()
with tempfile.TemporaryDirectory() as folder:
    path = Path(folder) / 'log.db'
    with sqlite3.connect(path) as db: GraphRepository.initialize_schema(db)
    db.close()
    repo = GraphRepository(str(path))
    cid = repo.insert_table_commands([draft])[0]
    saved = GraphRepository(str(path)).get_command(cid)
    assert saved.to_draft() == draft
    reopened = spec.create_editor(context=context, draft=saved.to_draft())
    assert reopened.get_draft() == draft
    reopened.close()
    output = []
    execution = ExecutionContext(variables={'名称': '任务A', '数量': 7}, output=output.append)
    executor = spec.create_executor()
    executor.execute_once(execution, saved)
    assert output == ['名称=任务A\n数量=7 / 7']
    execution.variables['数量'] = 8
    executor.execute_once(execution, saved)
    assert output[-1] == '名称=任务A\n数量=8 / 8'
    assert execution.variables == {'名称': '任务A', '数量': 8}
    output.clear()
    executor.execute(execution, saved)
    assert output == ['名称=任务A\n数量=8 / 8'] * 2
editor.close()
print('PASS: registration, variable sources, cursor insertion, repeated selection, refresh, multiline round trip, runtime values and repeat count')
