"""Regression tests use an offscreen Qt desktop; no real input is sent."""
import os
os.environ.setdefault('QT_QPA_PLATFORM', 'offscreen')

from types import SimpleNamespace
from unittest.mock import Mock, patch
import pytest
from PySide6.QtCore import QPoint, QPointF, QTimer, Qt
from PySide6.QtGui import QColor, QImage, QPainter
from PySide6.QtTest import QTest
from PySide6.QtWidgets import QApplication, QDialog, QWidget, QGraphicsScene

from instructions.common import actions
from instructions.common.editor import _PointSelectionDialog
from instructions.models import CommandRecord, ExecutionContext, InstructionDraft
from instructions.registry import get_instruction_spec
from instructions.键鼠.颜色判断.颜色判断 import rgb, InstructionExecutor
from node_editor.items import NodeItem
from node_editor.style import apply_theme


@pytest.fixture(scope='module')
def app():
    application = QApplication.instance() or QApplication([])
    yield application


@pytest.mark.parametrize('outcome', ['accept', 'escape', 'backend_error', 'construction_error'])
def test_real_nested_coordinate_dialog_preserves_editor(app, outcome):
    parent = QWidget()
    parent.setWindowOpacity(.8)
    parent.show()
    editor = get_instruction_spec('坐标点击').create_editor(parent)
    editor.setWindowOpacity(.9)
    original = editor._controls['坐标'].text()
    observations = []
    def create_picker(owner):
        if outcome == 'construction_error':
            raise RuntimeError('picker unavailable')
        picker = _PointSelectionDialog(owner)
        def select():
            observations.append((editor.isVisible(), parent.isVisible()))
            if outcome == 'escape':
                QTest.keyClick(picker, Qt.Key_Escape)
            else:
                QTest.mouseClick(picker, Qt.LeftButton, pos=QPoint(50, 50))
        QTimer.singleShot(20, select)
        return picker
    def acquire():
        editor._run_auxiliary('坐标')
        observations.append((editor.isVisible(), parent.isVisible()))
        editor.accept()
    gui = Mock()
    if outcome == 'backend_error':
        gui.position.side_effect = RuntimeError('display unavailable')
    else:
        gui.position.return_value = SimpleNamespace(x=-123, y=456)
    QTimer.singleShot(0, acquire)
    with patch('instructions.common.editor._PointSelectionDialog', side_effect=create_picker), \
         patch.object(actions, 'pyautogui_module', return_value=gui), \
         patch('instructions.common.editor.QMessageBox.warning') as warning:
        assert editor.exec() == QDialog.Accepted
        assert warning.call_count == int(outcome.endswith('error'))
    assert observations and all(all(item) for item in observations)
    assert editor.windowOpacity() == pytest.approx(.9, abs=.01)
    assert parent.windowOpacity() == pytest.approx(.8, abs=.01)
    assert editor._controls['坐标'].text() == ('-123,456' if outcome == 'accept' else original)
    parent.close()
    editor.deleteLater()
    parent.deleteLater()


@pytest.mark.parametrize('value,expected', [('#aAbB09',(170,187,9)), ('(1, 2, 255)',(1,2,255)), ([0,0,0],(0,0,0))])
def test_rgb_formats(value, expected):
    assert rgb(value) == expected


@pytest.mark.parametrize('value', ['#fff', '256,0,0', '-1,0,0', '1,2', '1.1,2,3', [True,2,3]])
def test_rgb_rejects_invalid_values(value):
    with pytest.raises(ValueError):
        rgb(value)


@pytest.mark.parametrize('actual,tolerance,mode,expected', [
    ((100,120,140),0,'相等',True), ((101,120,140),0,'相等',False),
    ((103,117,140),3,'相等',True), ((104,120,140),3,'相等',False),
    ((104,120,140),3,'不相等',True), ((100,120,140),0,'不相等',False),
])
def test_color_executor(actual,tolerance,mode,expected):
    gui = Mock()
    gui.pixel.return_value = actual
    context = ExecutionContext()
    command = CommandRecord(4,'颜色判断',{'坐标':'-50,80','颜色':'100,120,140','容差':tolerance,'比较':mode,'变量':'result'})
    with patch.object(actions,'pyautogui_module',return_value=gui):
        assert InstructionExecutor().execute(context,command) is expected
    gui.pixel.assert_called_once_with(-50,80)
    assert context.variables['result'] is expected
    assert context.metadata['flow_condition:4'] is expected


def test_color_backend_failure_and_stop():
    gui = Mock()
    gui.pixel.side_effect = OSError('no permission')
    command = CommandRecord(1,'颜色判断',{})
    with patch.object(actions,'pyautogui_module',return_value=gui):
        assert InstructionExecutor().execute(ExecutionContext(stop_requested=True),command) is None
        gui.pixel.assert_not_called()
        with pytest.raises(OSError):
            InstructionExecutor().execute(ExecutionContext(),command)


@pytest.mark.parametrize('result', [True, False])
def test_color_branch_roundtrip_and_execution(app, tmp_path, result):
    from graph_repository import GraphRepository
    from 数据库操作 import DatabaseOperation
    from main_work import CommandThread
    from openpyxl import Workbook
    db = DatabaseOperation(str(tmp_path/'color.db'))
    repo = GraphRepository(db.db_path)
    color = repo.add_command(InstructionDraft('颜色判断',{'坐标':'1,2','颜色':'#FFFFFF'}),unconnected=True)
    yes = repo.add_command(InstructionDraft('时间等待',{'时长':0}),unconnected=True)
    no = repo.add_command(InstructionDraft('时间等待',{'时长':0}),unconnected=True)
    nodes = {n.command_id:n.node_id for n in repo.snapshot().nodes}
    repo.connect_nodes('start',nodes[color.id])
    repo.connect_nodes(nodes[color.id],nodes[yes.id],kind=1)
    repo.connect_nodes(nodes[color.id],nodes[no.id],kind=2)
    repo.connect_nodes(nodes[yes.id],'end')
    repo.connect_nodes(nodes[no.id],'end')
    before = repo.validate_graph()
    book = Workbook()
    repo.export_to_workbook(book)
    repo.import_from_workbook(book)
    assert repo.snapshot().commands == before.commands
    assert repo.snapshot().edges == before.edges
    with patch('main_work.DatabaseOperation',return_value=db):
        thread = CommandThread(SimpleNamespace())
    executed=[]
    thread._execute_one = lambda command,context: (executed.append(command.id),result)[1]
    thread._persist_variables = lambda _:None
    thread._execute_flow(repo.execution_snapshot(),ExecutionContext())
    # Preserve existing linked-first, then unexecuted insertion-order semantics.
    assert executed[:2] == [color.id,yes.id if result else no.id]
    book.close()


@pytest.mark.parametrize('theme', ['light','dark'])
def test_node_halo_is_outside_shape_and_text_remains(app, tmp_path, theme):
    apply_theme(theme)
    node = NodeItem('test',1,'颜色判断','颜色判断',QColor('#8888dd'),control_kind_='condition')
    assert node.no_port is not None and node.output_port.link_kind == 1
    assert node.boundingRect().left() <= -10
    scene = QGraphicsScene()
    scene.addItem(node)
    def render(hover):
        node._hovered = hover
        node.update()
        image=QImage(340,210,QImage.Format_ARGB32)
        image.fill(QColor('#fafafa' if theme=='light' else '#09090b'))
        painter=QPainter(image)
        scene.render(painter)
        painter.end()
        return image
    plain=render(False)
    hovered=render(True)
    assert plain != hovered
    assert hovered.save(str(tmp_path/f'hover-{theme}.png'))
