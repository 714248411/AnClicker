import json
from types import SimpleNamespace
from unittest.mock import Mock, patch
import pytest
from PIL import Image
from instructions.models import ExecutionContext, CommandRecord, InstructionDraft
from instructions.registry import get_instruction_spec, INSTRUCTION_SPECS
from instructions.common import actions
from background_runtime import (BackgroundInput, Size, SESSION, ERROR, input_context,
    bind_background, close_background, current_backend, execute_background_method)
from background_catalog import values_for, label, METHODS

class Windows:
    target={'窗口句柄':'123','窗口标题':'测试','窗口类名':'fixture','进程ID':42,'进程路径':'fixture.exe'}
    def resolve(self, params):return dict(self.target)
    def validate(self, target):pass
    def size(self, target):return Size(200,150)

class Transport:
    def __init__(self, context):self.calls=[];self.closed=False
    def call(self, name, *args, **kwargs):
        self.calls.append((name,args))
        if name=='GetColor':return '112233'
        if name=='Capture':Image.new('RGB',(args[2]-args[0],args[3]-args[1]),(17,34,51)).save(args[4])
        if name=='GetClientSize':return {'value':1,'output':{'width':200,'height':150}}
        return 1
    def close(self):self.closed=True

@pytest.fixture
def bound():
    context=ExecutionContext(services={'background_windows':Windows,'background_transport':Transport})
    bind_background(context,{'绑定等待':0})
    backend=current_backend(context)
    yield context,backend
    close_background(context)

@pytest.mark.parametrize('type_id,parameters,expected',[
 ('坐标点击',{'坐标':'10,20','动作':'左键单击'},'LeftClick'),
 ('多坐标点击',{'坐标列表':'10,20;30,40','间隔':0},'LeftClick'),
 ('文本输入',{'内容':'中文后台','手动输入':False},'SendString'),
 ('颜色判断',{'坐标':'10,20','颜色':'#112233','容差':0,'变量':'matched'},'GetColor'),
 ('移动鼠标',{'类型':'指定坐标','坐标':'50,60','持续':0},'MoveTo'),
])
def test_existing_instructions_route_to_bound_window(bound,type_id,parameters,expected):
    context,backend=bound
    with patch.dict('sys.modules',{'pyautogui':Mock(side_effect=AssertionError('foreground')),'pyperclip':Mock()}):
        result=get_instruction_spec(type_id).create_executor().execute(context,CommandRecord(1,type_id,parameters))
    assert expected in [name for name,args in backend.transport.calls]
    if type_id=='文本输入':assert ('SendString',(123,'中文后台')) in backend.transport.calls
    if type_id=='颜色判断':assert context.variables['matched'] is True
    assert current_backend() is None

def test_failed_binding_never_falls_back_to_foreground():
    class Bad(Transport):
        def call(self,name,*args,**kw):raise RuntimeError('native error')
    context=ExecutionContext(services={'background_windows':Windows,'background_transport':Bad})
    with pytest.raises(RuntimeError):bind_background(context,{'绑定等待':0})
    assert ERROR in context.metadata and SESSION not in context.metadata
    with input_context(context),pytest.raises(RuntimeError,match='阻止前台'):
        actions.pyautogui_module()
    close_background(context)
    assert not context.metadata

def test_recorded_native_keys_and_wheel_route_to_backend(bound):
    from recorded_input import key_event,scroll_event,button_event
    context,backend=bound
    key_event(context,'win32:65:30:0',True,backend)
    key_event(context,'win32:65:30:0',False,backend)
    scroll_event(context,0,-2)
    with pytest.raises(ValueError):scroll_event(context,1,0)
    with pytest.raises(ValueError):button_event(context,'x1',True,backend)
    assert ('KeyDown',(65,)) in backend.transport.calls
    assert sum(n=='WheelDown' for n,a in backend.transport.calls)==2

def test_close_releases_held_inputs_and_session(bound):
    context,backend=bound
    backend.keyDown('ctrl');backend.mouseDown(button='left')
    close_background(context);close_background(context)
    assert backend.closed and backend.transport.closed
    assert ('KeyUp',(17,)) in backend.transport.calls
    assert ('LeftUp',()) in backend.transport.calls
    assert ('UnBindWindow',()) in backend.transport.calls

def test_screenshot_uses_exclusive_end_coordinates(bound):
    context,backend=bound
    image=backend.screenshot(region=(10,20,30,40))
    assert image.size==(30,40) and image.getpixel((0,0))==(17,34,51)
    assert backend.transport.calls[-1][1][:4]==(10,20,40,60)
    with pytest.raises(ValueError):backend.screenshot(region=(195,0,10,10))

def test_background_parameters_keep_int64_and_resolve_variables(bound):
    context,backend=bound
    context.variables['值']=2**45
    parameters={'接口':label('WriteInt'),'参数':json.dumps({'hwnd':'@窗口','addr':'1000','type':0,'v':'{{值}}'}),'变量':'result'}
    assert execute_background_method(context,'后台内存操作',parameters)==1
    assert backend.transport.calls[-1]==('WriteInt',(123,'1000',0,2**45))
    assert context.variables['result']==1
    with pytest.raises(ValueError):values_for('WriteInt',{'v':2**64})
    with pytest.raises(ValueError):values_for('GetColor',{'typo':1})

def test_ref_outputs_are_stored_as_structured_variable(bound):
    context,backend=bound
    result=execute_background_method(context,'后台窗口操作',{'接口':label('GetClientSize'),'参数':'{}','变量':'size'})
    assert result==context.variables['size']=={'value':1,'output':{'width':200,'height':150}}

def test_input_context_is_nested_and_does_not_leak(bound):
    context,backend=bound
    with input_context(context):
        assert current_backend() is backend
        with input_context(ExecutionContext()):assert current_backend() is None
        assert current_backend() is backend
    assert current_backend() is None

def test_closed_window_does_not_receive_more_input(bound):
    context,backend=bound
    backend.windows.validate=Mock(side_effect=RuntimeError('closed'))
    before=list(backend.transport.calls)
    with pytest.raises(RuntimeError):backend.click(1,2)
    assert backend.transport.calls==before

def test_every_method_editor_restores_typed_form_and_updates_values():
    from qt_compat.QtWidgets import QApplication
    app=QApplication.instance() or QApplication([])
    for spec in INSTRUCTION_SPECS:
        if spec.category!='后台功能' or not spec.type_id.startswith('后台'):continue
        editor=spec.create_editor()
        try:
            for name,item in METHODS.items():
                if item['group']!=spec.type_id:continue
                editor.load_draft(InstructionDraft(spec.type_id,{'接口':label(name),'参数':'{}','变量':''}))
                assert set(editor._arguments)=={p['name'] for p in item['args'] if not p['out'] or p.get('inout')}
                assert editor.get_draft().parameters['接口']==label(name)
        finally:editor.deleteLater()
    app.processEvents()


def test_capture_array_returns_actual_rgb_bytes(bound):
    import base64
    context,backend=bound
    result=execute_background_method(context,'后台图色操作',{'接口':'CaptureArray','参数':'{"x1":10,"y1":20,"x2":12,"y2":23}','变量':'array'})
    assert (result['width'],result['height'],result['format'])==(2,3,'RGB')
    assert base64.b64decode(result['data_base64'])==bytes((17,34,51))*6


def test_failed_write_is_an_execution_error_not_reported_as_success(bound):
    context,backend=bound
    backend.transport.call=Mock(return_value=0)
    with pytest.raises(RuntimeError,match='WriteInt'):
        execute_background_method(context,'后台内存操作',{'接口':'WriteInt','参数':'{"addr":"1000"}'})


def test_coordinate_conversion_preserves_input_coordinates():
    assert values_for('ClientToScreen',{'hwnd':123,'x':25,'y':30})==[123,25,30]


def test_component_configuration_protects_registration_code(tmp_path):
    from background_component_settings import read_config,write_config
    path=tmp_path/'config.json'
    write_config({'dll_path':'test.dll','reg_code':'test-local-secret','reg_extra':'local'},path)
    assert 'test-local-secret' not in path.read_text(encoding='utf8')
    assert read_config(path)['reg_code']=='test-local-secret'
