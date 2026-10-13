from unittest.mock import patch
import pytest
from flow_comments import BELOW, ABOVE, disabled_command_ids
from graph_repository import GraphRepository
from instructions.models import InstructionDraft, CommandRecord, ExecutionContext
from main_work import CommandThread
from 数据库操作 import DatabaseOperation


@pytest.mark.parametrize('types,expected', [
    (['时间等待', BELOW, '时间等待', ABOVE, '时间等待'], {1,2,3}),
    (['时间等待', BELOW, '时间等待'], {1,2}),
    (['时间等待', ABOVE, '时间等待'], {0,1}),
    ([BELOW, BELOW, '时间等待', ABOVE, '时间等待', ABOVE, '时间等待'], set(range(6))),
    ([BELOW, ABOVE, '时间等待', BELOW, ABOVE], {0,1,3,4}),
])
def test_ranges(types, expected):
    commands = [CommandRecord(i, kind, order=i) for i,kind in enumerate(types)]
    assert disabled_command_ids(commands) == expected
    assert disabled_command_ids(list(reversed(commands))) == expected


@pytest.mark.parametrize('jump', [False, True])
@pytest.mark.parametrize('linked', [False, True])
@pytest.mark.parametrize('mode', ['全部指令', '单行指令', '从当前行运行'])
def test_skip_ranges_all_runtime_entries(tmp_path, jump, linked, mode):
    db = DatabaseOperation(str(tmp_path / 'comments.db'))
    repo = GraphRepository(db.db_path)
    types = ['时间等待', BELOW, '运行Python', ABOVE, '时间等待']
    commands = [repo.add_command(InstructionDraft(kind, {}), unconnected=True) for kind in types]
    if jump:
        repo.add_command(InstructionDraft('报错跳转', {}), unconnected=True)
    nodes = {n.command_id:n.node_id for n in repo.snapshot().nodes}
    if linked:
        chain = ['start'] + [nodes[c.id] for c in commands] + ['end']
        for source,target in zip(chain, chain[1:]):
            repo.connect_nodes(source,target)
    with patch('main_work.DatabaseOperation', return_value=db):
        worker = CommandThread(type('Host', (), {})())
    worker.run_mode = (mode, commands[2].id)
    worker.run_unconnected = not linked
    executed = []
    worker._execute_one = lambda command, context: executed.append(command.id)
    worker._persist_variables = lambda values: None
    worker._execute_commands(worker._commands_for_mode(), ExecutionContext())
    expected = [commands[0].id,commands[4].id] if mode == '全部指令' else [] if mode == '单行指令' else [commands[4].id]
    assert executed == expected
    assert [c.type_id for c in repo.list_commands()][:5] == types


def test_marker_editor_and_excel_roundtrip(tmp_path):
    from qt_compat.QtWidgets import QApplication
    from instructions.registry import get_instruction_spec
    from openpyxl import Workbook
    app = QApplication.instance() or QApplication([])
    for kind in (BELOW, ABOVE):
        spec = get_instruction_spec(kind)
        assert spec.category == '流程'
        editor = spec.create_editor(draft=InstructionDraft(kind, repeat_count=9, note='保留'))
        assert editor.ui.repeatLabel.isHidden()
        assert editor.ui.repeatSpinBox.isHidden()
        assert editor.get_draft().repeat_count == 1
        assert editor.get_draft().note == '保留'
        assert editor.get_draft().type_id == kind
        editor.close()
        editor.deleteLater()
    app.processEvents()
    repo = GraphRepository(DatabaseOperation(str(tmp_path / 'source.db')).db_path)
    for kind in ('时间等待', BELOW, '时间等待', ABOVE, '时间等待'):
        repo.add_command(InstructionDraft(kind, {}), unconnected=True)
    workbook = Workbook()
    repo.export_to_workbook(workbook)
    restored = GraphRepository(DatabaseOperation(str(tmp_path / 'restored.db')).db_path)
    restored.import_from_workbook(workbook)
    assert [c.type_id for c in restored.list_commands()] == [c.type_id for c in repo.list_commands()]
    assert len(disabled_command_ids(restored.list_commands())) == 3
    workbook.close()


@pytest.mark.parametrize('kind', ['条件判断', '循环', '变量比较', '终止流程'])
def test_commented_control_never_changes_execution(tmp_path, kind):
    db = DatabaseOperation(str(tmp_path / 'control.db'))
    repo = GraphRepository(db.db_path)
    records = [repo.add_command(InstructionDraft(t, {}), unconnected=True)
               for t in (BELOW, kind, ABOVE, '时间等待')]
    nodes = {n.command_id:n.node_id for n in repo.snapshot().nodes}
    repo.connect_nodes('start', nodes[records[0].id])
    for source,target in zip(records, records[1:]):
        repo.connect_nodes(nodes[source.id], nodes[target.id])
    # Commented controls may have invalid parameters.
    with patch('main_work.DatabaseOperation', return_value=db):
        worker = CommandThread(type('Host', (), {})())
    worker.run_unconnected = False
    worker._persist_variables = lambda values: None
    executed = []
    worker._execute_one = lambda command, context: executed.append(command.id)
    worker._execute_flow(repo.execution_snapshot(), ExecutionContext())
    assert executed == [records[-1].id]


@pytest.mark.parametrize('markers', ['below', 'above', 'pair'])
def test_connected_ranges_follow_edges_not_table_order(tmp_path, markers):
    from flow_comments import snapshot_disabled_ids
    db = DatabaseOperation(str(tmp_path / 'directions.db'))
    repo = GraphRepository(db.db_path)
    # Deliberately insert the tail before the head.
    tail, middle, head = [repo.add_command(InstructionDraft('时间等待', {}), unconnected=True) for _ in range(3)]
    low = repo.add_command(InstructionDraft(BELOW, {}), unconnected=True) if markers != 'above' else None
    high = repo.add_command(InstructionDraft(ABOVE, {}), unconnected=True) if markers != 'below' else None
    branch = repo.add_command(InstructionDraft('时间等待', {}), unconnected=True)
    records = [head] + ([low] if low else []) + [middle] + ([high] if high else []) + [tail]
    nodes = {n.command_id:n.node_id for n in repo.snapshot().nodes}
    chain = ['start'] + [nodes[c.id] for c in records] + ['end']
    for source,target in zip(chain,chain[1:]):
        repo.connect_nodes(source,target)
    repo.connect_nodes(nodes[branch.id], 'end')
    expected = {middle.id} | ({low.id} if low else set()) | ({high.id} if high else set())
    if markers == 'below': expected.add(tail.id)
    if markers == 'above': expected.add(head.id)
    assert snapshot_disabled_ids(repo.snapshot()) == expected
    with patch('main_work.DatabaseOperation', return_value=db):
        worker = CommandThread(type('Host', (), {})())
    worker.run_unconnected = False
    worker._persist_variables = lambda values: None
    executed = []
    worker._execute_one = lambda command, context: executed.append(command.id)
    worker._execute_flow(repo.execution_snapshot(), ExecutionContext())
    assert set(executed) == {c.id for c in records if c.id not in expected}
