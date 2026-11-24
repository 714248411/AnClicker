"""Exercise real table and graph menus and persisted recursive folding."""
import os
import sys
import tempfile
from pathlib import Path
from types import SimpleNamespace
from unittest.mock import patch
if __package__ in (None, ''):
    sys.path.insert(0, str(Path(__file__).resolve().parents[1]))
from anclicker.platform.qt_compat.QtWidgets import QApplication, QTableWidgetItem, QMenu
from anclicker.platform.qt_compat.QtCore import Qt
from anclicker.platform.qt_compat.QtGui import QContextMenuEvent, QFontDatabase, QFont
from anclicker.domain.instructions import InstructionDraft
from anclicker.instructions.registry import iter_instruction_specs, get_instruction_spec
from anclicker.storage.database import DatabaseOperation
from anclicker.storage.graph_repository import GraphRepository
from anclicker.ui.instruction_table import InstructionTableWidget, INDENT_DEPTH_ROLE
from anclicker.ui.node_editor.widget import NodeEditorWidget
from anclicker.ui.instruction_workspace import InstructionWorkspace

os.environ.setdefault('QT_QPA_PLATFORM', 'offscreen')
app = QApplication.instance() or QApplication([])
font_id = QFontDatabase.addApplicationFont('C:/Windows/Fonts/msyh.ttc')
families = QFontDatabase.applicationFontFamilies(font_id)
if families: app.setFont(QFont(families[0], 10))
with tempfile.TemporaryDirectory() as folder:
    db = DatabaseOperation(str(Path(folder) / 'ui.db'))
    repo = GraphRepository(db.db_path)
    drafts = []
    for name in ('采集任务', '图片识别', '结果处理', '日志任务'):
        drafts.extend([InstructionDraft('多线程启动', {'线程名称':name, '入口编号':0}),
                       InstructionDraft('时间等待', {'时长':0}, note=name + '的步骤')])
    ids = repo.append_recording(drafts)
    table = InstructionTableWidget(0, 7)
    table.resize(960, 430)
    table.setHorizontalHeaderLabels(['行', '#', '命令', '参数', '次数', '异常', '备注'])
    table.setColumnWidth(0, 40); table.setColumnWidth(1, 40); table.setColumnWidth(2, 470)
    table.setColumnHidden(3, True); table.setColumnHidden(5, True)
    def refresh():
        commands = repo.list_commands()
        table.setRowCount(len(commands))
        for row, command in enumerate(commands):
            for col in range(7):
                text = command.type_id if col == 2 else command.note if col == 6 else str(row + 1)
                item = QTableWidgetItem(text); item.setData(Qt.UserRole, command.id)
                item.setToolTip(text)
                table.setItem(row, col, item)
        table.update_comment_ranges(repo.snapshot())
        app.processEvents()
    def nest(cid, enabled):
        repo.set_thread_nested(cid, enabled); refresh()
    def fold(cid):
        command = repo.get_command(cid)
        repo.set_step_collapsed(cid, not command.parameters.get('已折叠', True)); refresh()
    table.threadNestedRequested.connect(nest)
    table.stepFoldRequested.connect(fold)
    refresh(); table.show(); app.processEvents()
    assert all(table.isRowHidden(row) for row in (1,3,5,7))
    def table_menu(cid, chosen):
        row = next(i for i,c in enumerate(repo.list_commands()) if c.id == cid)
        point = table.visualRect(table.model().index(row, 2)).center()
        def execute(menu, *args):
            actions = {a.text():a for a in menu.actions()}
            assert '打开嵌套多线程' in actions and '取消嵌套多线程' in actions
            actions[chosen].trigger()
            return actions[chosen]
        with patch('anclicker.ui.instruction_table.exec_two_column_menu', execute):
            table.contextMenuEvent(QContextMenuEvent(QContextMenuEvent.Mouse, point, table.viewport().mapToGlobal(point)))
    table_menu(ids[2], '打开嵌套多线程')
    fold(ids[0])
    assert not table.isRowHidden(2) and table.isRowHidden(3)
    table_menu(ids[4], '打开嵌套多线程')
    fold(ids[2])
    assert not table.isRowHidden(4) and table.isRowHidden(5)
    assert table.item(2,2).data(INDENT_DEPTH_ROLE) == 1 and table.item(4,2).data(INDENT_DEPTH_ROLE) == 2
    assert table.item(0,2).text().startswith('▼') is False
    assert table.item(0,2).text().startswith('▾')
    fold(ids[0]); fold(ids[0])
    assert not table.isRowHidden(4) and table.isRowHidden(5), 'children retain their fold states'
    artifact = Path('artifacts/validation/thread-groups'); artifact.mkdir(parents=True, exist_ok=True)
    table.grab().save(str(artifact / 'nested-table.png'))
    print('PASS table nested menu signals, default folding, indentation and saved child fold states')
    widget = NodeEditorWidget(); widget.resize(1000, 700)
    specs = {s.type_id:s for s in iter_instruction_specs()}
    graph = repo.snapshot()
    widget.load_graph(graph.nodes, graph.edges, specs, allow_incomplete=True)
    InstructionWorkspace._apply_step_folds(SimpleNamespace(editor=widget), graph)
    scene = widget.scene
    scene.threadNestedRequested.connect(nest)
    widget.show(); widget.view.fit_graph(); app.processEvents()
    node = scene.nodes_by_command_id[ids[4]]
    assert node.node_id in scene.locked_groups
    point = widget.view.mapFromScene(node.mapToScene(node.boundingRect().center()))
    def graph_execute(menu, *args):
        actions = {a.text():a for a in menu.actions()}
        assert '打开嵌套多线程' in actions and '取消嵌套多线程' in actions
        return actions['取消嵌套多线程']
    with patch('anclicker.ui.node_editor.view.exec_two_column_menu', graph_execute):
        widget.view.contextMenuEvent(QContextMenuEvent(QContextMenuEvent.Mouse, point, widget.view.mapToGlobal(point)))
    assert repo.get_command(ids[4]).parameters['嵌套层级'] == 1
    editor = get_instruction_spec('多线程启动').create_editor()
    assert editor.get_draft().parameters['入口编号'] == 0
    print('PASS graph menu, locked group layout and connected-entry editor default')
    editor.close(); widget.close(); table.close()
print('PASS thread group UI suite')
