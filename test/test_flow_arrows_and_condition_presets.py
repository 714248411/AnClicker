import math
from dataclasses import dataclass
from types import SimpleNamespace
from unittest.mock import patch
import pytest
from qt_compat.QtCore import QPointF, QRectF
from qt_compat.QtGui import QPainterPath, QTransform
from node_editor.flow_arrows import control_edges, arrow_segments, moving_arrows, arrow_repaint_region
from node_editor.scene import NodeScene
from node_editor.view import NodeView
from flow_condition_checks import evaluate, validate_parameters
from flow_condition_editor import ConditionPanel
from instructions.models import ExecutionContext, InstructionDraft
from instructions.registry import get_instruction_spec
from test.test_background_presets import app
from test.test_control_priority import Graph


@dataclass(eq=False)
class Node:
    control_kind: str = ''


@dataclass(eq=False)
class Edge:
    source_node: Node
    target_node: Node
    link_kind: int = 0


def test_arrows_cover_two_control_steps_and_error_links_without_sibling_paths():
    nodes = [Node() for _ in range(9)]
    nodes[4].control_kind = 'condition'
    edges = [Edge(a, b) for a, b in zip(nodes, nodes[1:])]
    sibling = Edge(nodes[3], Node())
    error = Edge(nodes[4], Node(), 5)
    branch = Edge(nodes[4], Node(), 2)
    extra = Edge(branch.target_node, Node())
    far = Edge(extra.target_node, Node())
    error_continuation = Edge(error.target_node, Node())
    selected = control_edges(edges + [sibling, error, branch, extra, far, error_continuation])
    assert set(selected) == set(edges[2:6] + [branch, extra, error])
    assert control_edges([Edge(Node(), Node())]) == ()


def test_loop_cycles_and_conditional_jump_branches_have_direction_markers():
    loop, a, b, after = Node('loop'), Node(), Node(), Node()
    edges = [Edge(loop,a,3), Edge(a,b), Edge(b,loop), Edge(loop,after,4)]
    assert set(control_edges(edges)) == set(edges)
    condition = Node('condition')
    jumps = [Edge(condition,a,7), Edge(condition,b,8), Edge(a,after,6)]
    assert set(control_edges(jumps)) == set(jumps)


def tips(path):
    return [QPointF(path.elementAt(i).x, path.elementAt(i).y) for i in range(1, path.elementCount(), 3)]


@pytest.mark.parametrize('zoom', [.05, .25, 1, 4, 64])
def test_arrows_keep_screen_spacing_size_and_speed_at_every_zoom(zoom):
    path = QPainterPath(QPointF(0,0)); path.lineTo(10000,0)
    transform = QTransform().scale(zoom,zoom)
    segments, total = arrow_segments(path,transform)
    viewport = QRectF(0,-20,400,40)
    first = moving_arrows(segments,total,viewport,0)
    second = moving_arrows(segments,total,viewport,.1)
    positions = tips(first)
    assert len(positions) > 3
    assert positions[1].x()-positions[0].x() == pytest.approx(36)
    assert first.elementAt(1).x-first.elementAt(0).x == pytest.approx(8)
    assert abs(first.elementAt(1).y-first.elementAt(0).y) == pytest.approx(4)
    assert tips(second)[0].x()-positions[0].x() == pytest.approx(3.6)


def test_long_offscreen_paths_are_clipped_without_changing_direction_or_spacing():
    path = QPainterPath(QPointF(1e9,0)); path.lineTo(-1e9,0)
    segments,total = arrow_segments(path,QTransform())
    result = moving_arrows(segments,total,QRectF(-200,-20,400,40),0)
    positions = tips(result)
    assert 5 < len(positions) < 15
    assert positions[0].x()-positions[1].x() == pytest.approx(36)
    assert result.elementAt(1).x < result.elementAt(0).x


def test_animation_timer_only_runs_for_visible_control_graphs_and_survives_reload(app):
    scene = NodeScene()
    view = NodeView(scene)
    view.resize(900,600)
    nodes = [{'id':i,'type_id':'条件判断' if i == 2 else '时间等待', 'x':i*250,'y':100}
             for i in range(5)]
    try:
        scene.load_graph(nodes,[],{})
        view.show(); view.fit_graph(); app.processEvents()
        assert not view._arrow_timer.isActive()
        view.play_run_animation()
        assert view._arrow_timer.isActive()
        for zoom in (.000001,.05,.5,1,64):
            view._set_zoom(zoom)
            assert not view.grab().isNull()
        view.hide(); app.processEvents()
        assert not view._arrow_timer.isActive()
        view.show(); app.processEvents()
        scene.load_graph([dict(n,type_id='时间等待') for n in nodes],[],{})
        app.processEvents()
        assert not scene.flow_arrow_edges and not view._arrow_timer.isActive()
        scene.clear()
        assert not view.grab().isNull()
    finally:
        view.close(); view.deleteLater(); app.processEvents()


@pytest.mark.parametrize('kind,key', [('图片存在','图像路径'), ('图片文件存在','图像路径'), ('OCR文字存在','目标文字')])
def test_common_presets_need_only_one_target_and_roundtrip_variables(app,kind,key):
    editor = get_instruction_spec('条件判断').create_editor()
    try:
        panel = editor.condition_panel
        panel.kind.setCurrentText(kind)
        panel.controls[key].setCurrentText('{{自定义目标}}')
        draft = editor.get_draft()
        assert draft.parameters[key] == '{{自定义目标}}'
        assert panel.advanced_panel.isHidden()
        assert [key for key in ('图像路径','目标文字','坐标','颜色') if not panel.rows[key].isHidden()] == [key]
        editor.load_draft(draft)
        assert editor.get_draft().parameters == draft.parameters
        panel.advanced_button.click()
        assert not panel.advanced_panel.isHidden()
    finally:
        editor.deleteLater()


def test_legacy_text_condition_and_variable_suggestions_preserve_saved_target(app):
    panel = ConditionPanel()
    try:
        panel.load({'判断类型':'文字存在','目标文字':'手动内容','精度':.95,'满足条件':'不存在 / 不相等'})
        panel.set_suggestions({'target_variables':['OCR文字','图片路径'], 'condition_suggestions':[]})
        assert panel.parameters()['判断类型'] == 'OCR文字存在'
        assert panel.parameters()['目标文字'] == '手动内容'
        assert panel.controls['目标文字'].findText('{{OCR文字}}') >= 0
        assert not panel.advanced_panel.isHidden()
        assert NodeScene._node_subtitle('条件循环',dict(panel.parameters(),方式='条件'),1) == '条件：OCR文字不存在：手动内容'
    finally:
        panel.deleteLater()


def test_file_predicate_checks_exact_project_path_without_screen_or_resource_fallback(tmp_path):
    project = tmp_path/'project'; project.mkdir()
    path = project/'目标.png'; path.write_bytes(b'fixture')
    database = SimpleNamespace(extract_resource_folder_path=lambda:[str(project)])
    context = ExecutionContext(variables={'图片':'目标.png'}, metadata={'project_path':str(project/'project.xlsx'),'database':database})
    parameters = {'判断类型':'图片文件存在','图像路径':'{{图片}}'}
    with patch('instructions.common.actions.pyautogui_module',side_effect=AssertionError('must not capture')):
        assert evaluate(context,parameters) is True
        context.variables['图片'] = str(tmp_path/'missing'/'目标.png')
        assert evaluate(context,parameters) is False
        assert evaluate(context,dict(parameters,满足条件='不存在 / 不相等')) is True
        context.variables['图片'] = str(project)
        assert evaluate(context,parameters) is False


@pytest.mark.parametrize('kind,key', [('图片存在','图像路径'),('图片文件存在','图像路径'),('OCR文字存在','目标文字')])
def test_missing_or_empty_target_variable_is_a_configuration_error(kind,key):
    parameters = {'判断类型':kind,key:'{{缺失}}','满足条件':'不存在 / 不相等'}
    with pytest.raises(KeyError,match='判断变量不存在'):
        evaluate(ExecutionContext(),parameters)
    with pytest.raises(ValueError,match='不能为空'):
        evaluate(ExecutionContext(variables={'缺失':None}),parameters)


def test_image_and_ocr_predicates_resolve_one_target_variable_without_side_effects(tmp_path):
    image = tmp_path/'image.png'; image.write_bytes(b'fixture')
    rows = [{'text':'任务完成','score':.99,'box':[[0,0],[20,0],[20,10],[0,10]]}]
    context = ExecutionContext(variables={'图片':str(image),'文字':'完成','范围':'0,0,200,200'},
        services={'本地OCR':lambda **kwargs:rows},metadata={'last_ocr_text':'保留'})
    parameters = {'判断类型':'图片存在','图像路径':'{{ 图片 }}','区域':'{{范围}}'}
    validate_parameters(parameters)
    with patch('instructions.common.actions.pyautogui_module') as gui, patch('instructions.common.image_match.best_image_match',return_value=None) as match:
        assert evaluate(context,parameters) is False
        assert match.call_args.kwargs['region'] == (0,0,200,200)
        gui.return_value.click.assert_not_called()
    assert evaluate(context,{'判断类型':'OCR文字存在','目标文字':'{{文字}}'}) is True
    assert evaluate(context,{'判断类型':'OCR文字存在','目标文字':'{{文字}}','满足条件':'不存在 / 不相等'}) is False
    assert context.metadata['last_ocr_text'] == '保留' and len(context.variables) == 3


@pytest.mark.parametrize('exists', [False,True])
def test_file_condition_routes_yes_and_no_in_actual_flow(tmp_path,exists):
    image = tmp_path/'image.png'
    if exists: image.write_bytes(b'fixture')
    g = Graph(tmp_path/'flow.db')
    condition = g.add('condition','条件判断',判断类型='图片文件存在',图像路径=str(image))
    yes,no = g.add('yes'),g.add('no')
    g.link('start',condition);g.link(condition,yes,1);g.link(condition,no,2)
    assert g.run() == ['condition','yes' if exists else 'no']


def test_animation_repaint_is_limited_to_visible_line_corridor():
    path = QPainterPath(QPointF(-1e9,50));path.lineTo(1e9,50)
    segments, _ = arrow_segments(path,QTransform())
    region = arrow_repaint_region(segments,QRectF(0,0,900,600))
    assert region.boundingRect().width() == 900
    assert region.boundingRect().height() == 24
