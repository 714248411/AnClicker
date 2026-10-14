import json
import threading
from types import SimpleNamespace
from unittest.mock import patch
from zipfile import ZipFile
from xml.sax.saxutils import escape
import pytest
from PIL import Image
from instructions.models import CommandRecord, ExecutionContext, InstructionDraft
from instructions.registry import get_instruction_spec
from flow_condition_context import condition_hint
from flow_condition_checks import evaluate
from background_preload import Preparation
from test.test_control_priority import Graph
from test.test_background_presets import app


def test_exact_user_loop_three_passes_then_mouse(tmp_path):
    g = Graph(tmp_path/'flow.db')
    image = g.add('image', '图像点击', 图像路径='fixture.png')
    wait = g.add('wait', '时间等待', 时长=2)
    move = g.add('move', '移动鼠标', 坐标='313,35')
    loop = g.add('loop', '循环', 次数=3, 方式='次数', 条件='True')
    g.link('start', image)
    g.link(image, wait)
    g.link(wait, move)
    g.link(wait, loop)
    g.link(loop, image, 3)
    g.link(move, 'end')
    assert [n for n in g.run() if n != 'loop'] == ['image', 'wait']*3 + ['move']


def test_loop_default_is_count_only_with_expandable_advanced(app):
    editor = get_instruction_spec('循环').create_editor()
    try:
        assert editor.mode_combo.currentText() == '次数'
        assert editor.advanced_panel.isHidden()
        assert not editor.count_spin.isHidden()
        assert editor.get_draft().parameters['次数'] == 3
        editor.advanced_button.click()
        assert not editor.advanced_panel.isHidden()
        assert editor.mode_combo.parent() is editor.advanced_panel
        editor.count_spin.setValue(5)
        draft = editor.get_draft()
        assert draft.parameters['方式'] == '次数' and draft.parameters['次数'] == 5
    finally:
        editor.deleteLater()


def test_nearest_five_prefers_color_over_older_image_and_respects_limit(tmp_path):
    g = Graph(tmp_path/'hints.db')
    g.add('image', '图像点击', 图像路径='a.png')
    g.add('color', '颜色判断', 坐标='10,20', 颜色='#112233', 容差=4)
    cond = g.add('condition', '条件判断', 条件='True')
    cid = next(k for k,v in g.names.items() if v == 'condition')
    hint = condition_hint(g.repo.snapshot(), cid)
    assert hint['condition_suggestions'][0]['parameters']['判断类型'] == '颜色判断'
    for i in range(5):
        g.add('gap'+str(i))
    assert not condition_hint(g.repo.snapshot())['condition_suggestions']


def test_new_visual_editor_infers_but_never_overwrites_saved_settings(app):
    hint = {'variable':'', 'candidates':[], 'condition_suggestions':[
        {'type_id':'图像点击', 'parameters':{'判断类型':'图片存在','图像路径':'a.png','精度':.9}}]}
    context = ExecutionContext(metadata={'condition_hint':lambda:hint})
    editor = get_instruction_spec('条件判断').create_editor(context=context)
    try:
        assert editor.get_draft().parameters['图像路径'] == 'a.png'
        manual = InstructionDraft('条件判断', {'判断类型':'颜色判断','坐标':'5,6','颜色':'#123456'})
        editor.load_draft(manual)
        editor._infer_condition(False)
        assert editor.get_draft().parameters['坐标'] == '5,6'
        editor.infer_condition_button.click()
        assert editor.get_draft().parameters['判断类型'] == '图片存在'
    finally:
        editor.deleteLater()


def test_visual_condition_color_is_boolean_and_selects_yes_branch(tmp_path):
    g = Graph(tmp_path/'branches.db')
    node = g.add('condition','条件判断', 判断类型='颜色判断', 坐标='1,2', 颜色='#112233')
    yes, no = g.add('yes'), g.add('no')
    g.link('start',node); g.link(node,yes,1); g.link(node,no,2)
    with patch('instructions.common.actions.pyautogui_module', return_value=SimpleNamespace(pixel=lambda *args:(17,34,51))):
        assert g.run() == ['condition','yes']


def test_image_missing_is_an_error_not_a_false_negative(tmp_path):
    with pytest.raises(FileNotFoundError):
        evaluate(ExecutionContext(), {'判断类型':'图片存在','图像路径':str(tmp_path/'missing.png')})
    path = tmp_path/'fixture.png'; Image.new('RGB',(3,3)).save(path)
    with patch('instructions.common.actions.pyautogui_module') as gui, patch('instructions.common.image_match.best_image_match', return_value=(0,0)):
        assert evaluate(ExecutionContext(), {'判断类型':'图片存在','图像路径':str(path)}) is True
        gui.return_value.click.assert_not_called()


@pytest.mark.parametrize('value,expected', [(None,False),([],False),([0,0],True),({'x':1,'y':2},True),({'x':1},False),('bad',False)])
def test_coordinate_checks_result_variable(value,expected):
    assert evaluate(ExecutionContext(variables={'point':value}), {'判断类型':'坐标存在','坐标':'{{point}}'}) is expected


def test_text_condition_does_not_click_or_overwrite_previous_ocr():
    rows=[{'text':'完成','score':.99,'box':[[0,0],[20,0],[20,10],[0,10]]}]
    context=ExecutionContext(variables={'OCR坐标':'old'},services={'本地OCR':lambda **kwargs:rows},metadata={'last_ocr_text':'old text'})
    assert evaluate(context,{'判断类型':'文字存在','目标文字':'完成'}) is True
    assert evaluate(context,{'判断类型':'文字存在','目标文字':'不存在'}) is False
    assert context.variables == {'OCR坐标':'old'} and context.metadata['last_ocr_text']=='old text'


def test_preparation_is_nonblocking_unbound_and_handed_off_once():
    ready=threading.Event()
    transport=SimpleNamespace(context=None,close=lambda:None)
    def factory(context):
        ready.wait(2)
        transport.context=context
        return transport
    pending=Preparation(factory,None)
    assert not pending.done.is_set()
    ready.set()
    context=ExecutionContext()
    assert pending.take(context) is transport
    assert transport.context is context
    assert pending.take(context) is None


def test_cancelled_preparation_closes_finished_helper():
    ready=threading.Event(); closed=threading.Event()
    def factory(context):
        ready.wait(2)
        return SimpleNamespace(close=closed.set)
    pending=Preparation(factory,None)
    pending.cancel();ready.set()
    assert pending.done.wait(2) and closed.wait(2)


def bank(tmp_path, body):
    path=tmp_path/'bank.docx'
    with ZipFile(path,'w') as z:
        z.writestr('word/document.xml','<w:document xmlns:w="http://schemas.openxmlformats.org/wordprocessingml/2006/main"><w:body>'+body+'</w:body></w:document>')
    return path

def paragraph(text):
    return '<w:p><w:r><w:t>'+escape(text)+'</w:t></w:r></w:p>'


def test_local_word_answers_paragraphs_and_variables(tmp_path):
    path=bank(tmp_path,paragraph('题目：天空是什么颜色？')+paragraph('答案：蓝色'))
    context=ExecutionContext(variables={'题目':'天空是什么颜色？'})
    command=CommandRecord(1,'后台答题器',{'题库路径':str(path),'题目来源':'变量','题目':'题目','变量':'答案'})
    result=get_instruction_spec('后台答题器').create_executor().execute(context,command)
    assert result=='蓝色' and context.variables['答案']=='蓝色'
    assert get_instruction_spec('后台答题器').display_name=='本地Word答题器'


def test_local_word_table_and_conflicting_answers(tmp_path):
    from local_word_answers import load_bank,find_answer
    row=lambda a,b:'<w:tr><w:tc>'+paragraph(a)+'</w:tc><w:tc>'+paragraph(b)+'</w:tc></w:tr>'
    path=bank(tmp_path,'<w:tbl>'+row('题目','答案')+row('1+1','2')+'</w:tbl>')
    assert find_answer(load_bank(path),'1+1')['answer']=='2'
    assert find_answer(load_bank(path),'question') is None
    with pytest.raises(ValueError,match='答案不同'):
        find_answer([('q','a'),('q','b')],'q')


def test_word_editor_has_local_fields_only(app):
    editor=get_instruction_spec('后台答题器').create_editor()
    try:
        assert '接口' not in editor._controls
        editor._controls['题库路径'].setText('bank.docx')
        editor._controls['题目'].setText('q')
        assert editor.get_draft().parameters['变量']=='答案'
    finally:
        editor.deleteLater()
