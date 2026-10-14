import json
from unittest.mock import patch
import pytest
from instructions.models import InstructionDraft, CommandRecord
from instructions.registry import get_instruction_spec
from background_catalog import label, values_for
from test.test_background_runtime import bound


def create(method, values=None):
    from background_catalog import METHODS
    return get_instruction_spec(METHODS[method]['group']).create_editor(draft=InstructionDraft(
        METHODS[method]['group'], {'接口': label(method), '参数': json.dumps(values or {}, ensure_ascii=False), '变量': '结果'}))


def parameters(editor):
    return json.loads(editor.get_draft().parameters['参数'])


def test_existing_find_image_values_survive_collapsed_form_and_method_switch():
    saved = dict(x1=-10, y1=20, x2=100, y2=180, pic_name='a.bmp|b.png', sim=.92345, delta_color='102030', dir=3)
    editor = create('FindPic', saved)
    try:
        assert editor.advanced_panel.isHidden()
        assert '已有自定义配置' in editor.advanced_button.text()
        assert editor._argument_widgets['区域'].text() == '-10,20,110,160'
        assert parameters(editor) == saved
        editor._controls['接口'].setCurrentText(label('GetColor'))
        editor._controls['接口'].setCurrentText(label('FindPic'))
        assert parameters(editor) == saved
        editor.advanced_button.setChecked(True)
        assert values_for('FindPic', parameters(editor)) == values_for('FindPic', saved)
    finally:
        editor.deleteLater()


def test_region_edit_stores_backend_corners_and_executes_same_bounds(bound):
    context, backend = bound
    editor = create('Capture', {'file': 'unused.bmp'})
    try:
        editor._argument_widgets['区域'].setText('10,20,30,40')
        values = parameters(editor)
        assert [int(values[k]) for k in ('x1','y1','x2','y2')] == [10,20,40,60]
        with patch.object(backend.transport, 'call', return_value=1) as call:
            draft = editor.get_draft()
            get_instruction_spec(draft.type_id).create_executor().execute(context, CommandRecord(1,draft.type_id,draft.parameters))
        assert call.call_args.args[:5] == ('Capture',10,20,40,60)
    finally:
        editor.deleteLater()


def test_invalid_visible_region_cannot_save_stale_valid_corners():
    editor = create('FindStr')
    try:
        field = editor._argument_widgets['区域']
        field.setText('10,20,')
        with pytest.raises(ValueError, match='范围'):
            editor.get_draft()
        field.setText('10,20,-3,40')
        with pytest.raises(ValueError, match='大于零'):
            editor.get_draft()
        field.setText('10,20,30,40')
        assert int(parameters(editor)['x2']) == 40
    finally:
        editor.deleteLater()


def test_variable_bounds_and_precision_roundtrip_without_forced_numeric_defaults():
    saved = dict(x1='{{左}}', y1='{{上}}', x2='{{右}}', y2='{{下}}', sim='{{精度}}', str='确定')
    editor = create('FindStr', saved)
    try:
        assert parameters(editor) == saved
        assert '变量坐标' in editor._argument_widgets['区域'].placeholderText()
        assert not editor._argument_widgets['sim'].slider.isEnabled()
        editor._arguments['str'].setText('继续')
        assert parameters(editor) == dict(saved, str='继续', color='ffffff-000000')
        editor._argument_widgets['区域'].setText('0,0,20,30')
        assert parameters(editor)['sim'] == '{{精度}}'
        assert [parameters(editor)[k] for k in ('x1','y1','x2','y2')] == ['0','0','20','30']
    finally:
        editor.deleteLater()


@pytest.mark.parametrize('method,initial,expected', [('FindPic',.92345,'0.8'),('FindPicSim',93,'80')])
def test_precision_slider_uses_each_methods_original_scale(method, initial, expected):
    editor = create(method, {'sim':initial})
    try:
        assert parameters(editor)['sim'] == initial
        editor._argument_widgets['sim'].slider.setValue(80)
        assert parameters(editor)['sim'] == expected
    finally:
        editor.deleteLater()


def test_key_capture_uses_foreground_names_but_keeps_backend_key_codes(bound):
    context, backend = bound
    editor = create('KeyPress', {'vk':'0x41'})
    try:
        assert parameters(editor)['vk'] == '0x41'
        field = editor._argument_widgets['按键']
        field.setCurrentText('enter')
        assert int(parameters(editor)['vk']) == 13
        field.apply_capture('f8')
        assert int(parameters(editor)['vk']) == 119
        with pytest.raises(ValueError, match='单个按键'):
            field.apply_capture('ctrl+v')
        assert int(parameters(editor)['vk']) == 119
        draft = editor.get_draft()
        get_instruction_spec(draft.type_id).create_executor().execute(context, CommandRecord(1,draft.type_id,draft.parameters))
        assert ('KeyPress',(119,)) in backend.transport.calls
    finally:
        editor.deleteLater()


def test_multiline_paste_and_bound_window_override_are_preserved(bound):
    context, backend = bound
    context.variables['内容'] = '变量替换'
    editor = create('SendString', {'hwnd':'@窗口','str':'旧内容'})
    try:
        field = editor._argument_widgets['str']
        field.editor.setPlainText('第一行\n第二行 {{内容}}')
        with patch('instructions.common.input_controls.clipboard_text',return_value='追加文字'):
            field.editor.moveCursor(field.editor.textCursor().End)
            field.paste_button.click()
        assert parameters(editor)['str']=='第一行\n第二行 {{内容}}追加文字'
        draft=editor.get_draft()
        get_instruction_spec(draft.type_id).create_executor().execute(context,CommandRecord(1,draft.type_id,draft.parameters))
        assert ('SendString',(123,'第一行\n第二行 变量替换追加文字')) in backend.transport.calls
        editor._arguments['hwnd'].setText('{{目标窗口}}')
        assert parameters(editor)['hwnd']=='{{目标窗口}}'
    finally:
        editor.deleteLater()


def test_editable_direction_preserves_variable_and_updates_choice_value():
    editor=create('FindPic',{'dir':'{{方向}}'})
    try:
        field=editor._argument_widgets['dir']
        assert field.currentText()=='{{方向}}'
        assert parameters(editor)['dir']=='{{方向}}'
        field.setCurrentText('2')
        assert parameters(editor)['dir']=='2'
    finally:
        editor.deleteLater()


def test_point_edits_support_independent_variables():
    editor=create('MoveTo',{'x':20,'y':30})
    try:
        editor._argument_widgets['坐标'].setText('{{横坐标}},{{纵坐标}}')
        assert parameters(editor)=={'x':'{{横坐标}}','y':'{{纵坐标}}'}
        editor._arguments['x'].setText('70')
        assert editor._argument_widgets['坐标'].text()=='70,{{纵坐标}}'
    finally:
        editor.deleteLater()


@pytest.mark.parametrize('method',['FoobarDrawLine','ScreenToClient','GetPointWindow'])
def test_unrelated_line_endpoints_and_screen_coordinates_keep_native_fields(method):
    editor=create(method)
    try:
        assert '区域' not in editor._argument_widgets and '坐标' not in editor._argument_widgets
        editor._arguments['x1' if method=='FoobarDrawLine' else 'x'].setText('45')
        values=parameters(editor)
        assert values['x1' if method=='FoobarDrawLine' else 'x']=='45'
    finally:
        editor.deleteLater()
