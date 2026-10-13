import json
from unittest.mock import Mock,patch
import pytest
from qt_compat.QtWidgets import QApplication
from background_binding import AUTO,CUSTOM,binding_attempts
from background_runtime import bind_background,close_background,current_backend,ERROR
from background_catalog import label
from instructions.models import ExecutionContext,InstructionDraft
from instructions.registry import get_instruction_spec
from test.test_background_runtime import Windows,Transport

@pytest.fixture
def app():
    return QApplication.instance() or QApplication([])

def test_default_prefers_dx1_then_dx2_using_actual_plugin_names():
    attempts,delay=binding_attempts({})
    assert attempts==[('DX1','dx','dx','dx',0),('DX2','dx2','dx2','dx',0)]
    assert delay==1

def test_old_explicit_modes_keep_legacy_defaults():
    assert binding_attempts({'图像模式':'gdi'})[0]==[(CUSTOM,'gdi','windows','windows',0)]
    assert binding_attempts({'图像模式':'dx1','鼠标模式':'dx1','键盘模式':'dx1'})[0]==[(CUSTOM,'dx','dx','dx',0)]

@pytest.mark.parametrize('parameters',[{'绑定方案':'missing'},{'绑定模式':1},{'绑定等待':float('nan')},{'绑定等待':-1},{'绑定方案':CUSTOM,'图像模式':'normal'}])
def test_invalid_binding_configuration_is_rejected(parameters):
    with pytest.raises(ValueError):binding_attempts(parameters)

def test_dx_failure_releases_first_host_and_retries_dx2():
    created=[]
    class Retry(Transport):
        def __init__(self,context):super().__init__(context);created.append(self)
        def call(self,name,*args,**kwargs):
            result=super().call(name,*args,**kwargs)
            return 0 if name=='BindWindow' and args[1]=='dx' else result
    context=ExecutionContext(services={'background_windows':Windows,'background_transport':Retry})
    try:
        bind_background(context,{'绑定等待':0})
        assert len(created)==2 and created[0].closed and not created[1].closed
        assert current_backend(context).binding_profile=='DX2' and ERROR not in context.metadata
        assert [a[1:] for t in created for n,a in t.calls if n=='BindWindow']==[('dx','dx','dx',0),('dx2','dx2','dx',0)]
    finally:close_background(context)
    assert all(t.closed for t in created)

def test_failed_modes_remain_blocked_from_foreground_and_stop_never_retries():
    for stop in (False,True):
        created=[]
        class Bad(Transport):
            def __init__(self,context):super().__init__(context);created.append(self);self.context=context
            def call(self,name,*args,**kwargs):
                if name=='BindWindow':self.context.stop_requested=stop;return 0
                return super().call(name,*args,**kwargs)
        context=ExecutionContext(services={'background_windows':Windows,'background_transport':Bad})
        with pytest.raises(RuntimeError):bind_background(context,{'绑定等待':0})
        assert len(created)==(1 if stop else 2) and all(t.closed for t in created)
        assert ERROR in context.metadata
        with pytest.raises(RuntimeError):current_backend(context)
        close_background(context)

def test_component_initialization_failure_does_not_retry():
    factory=Mock(side_effect=RuntimeError('missing component'))
    context=ExecutionContext(services={'background_windows':Windows,'background_transport':factory})
    with pytest.raises(RuntimeError,match='missing component'):bind_background(context,{})
    factory.assert_called_once();assert ERROR in context.metadata

def test_binding_editor_presets_and_legacy_roundtrip(app):
    editor=get_instruction_spec('绑定选择窗口').create_editor()
    try:
        assert editor.get_draft().parameters['绑定方案']==AUTO
        assert editor.advanced_panel.isHidden()
        editor._controls['绑定方案'].setCurrentText('DX2')
        params=editor.get_draft().parameters
        assert (params['图像模式'],params['鼠标模式'],params['键盘模式'])==('dx2','dx2','dx')
        assert not editor._controls['图像模式'].isEnabled()
        editor.load_draft(InstructionDraft('绑定选择窗口',{'图像模式':'gdi','窗口标题':'旧窗口'}))
        params=editor.get_draft().parameters
        assert params['绑定方案']==CUSTOM
        assert (params['图像模式'],params['鼠标模式'],params['键盘模式'])==('gdi','windows','windows')
        assert params['窗口标题']=='旧窗口' and editor._controls['图像模式'].isEnabled()
    finally:editor.deleteLater()

def test_operation_search_preserves_arguments_and_accepts_api_name(app):
    editor=get_instruction_spec('后台图色操作').create_editor()
    try:
        editor._controls['接口'].setCurrentText(label('FindPic'))
        editor._arguments['pic_name'].setText('example.bmp')
        editor._controls['接口'].setEditText('getco')
        assert editor._arguments['pic_name'].text()=='example.bmp'
        editor._controls['接口'].setEditText('getcolor')
        assert editor.get_draft().parameters['接口']==label('GetColor')
        editor._controls['接口'].setCurrentText(label('FindPic'))
        assert editor._arguments['pic_name'].text()=='example.bmp'
    finally:editor.deleteLater()

def test_file_choosers_write_multi_image_paths_and_use_save_dialog(app):
    editor=get_instruction_spec('后台图色操作').create_editor()
    try:
        editor._controls['接口'].setCurrentText(label('FindPic'))
        control=editor._arguments['pic_name']
        with patch('instructions.common.background_instruction.QFileDialog.getOpenFileNames',return_value=(['C:/a.bmp','C:/b.png'],'')):
            editor._browse_argument('FindPic','pic_name',control)
        assert json.loads(editor.get_draft().parameters['参数'])['pic_name']=='C:/a.bmp|C:/b.png'
        with patch('instructions.common.background_instruction.QFileDialog.getSaveFileName',return_value=('C:/out.bmp','')) as save:
            editor._browse_argument('ImageToBmp','bmp_name',control)
        save.assert_called_once();assert control.text()=='C:/out.bmp'
    finally:editor.deleteLater()


def test_auto_falls_back_when_dx1_binds_but_capture_fails():
    created=[]
    class NoImage(Transport):
        def __init__(self,context):super().__init__(context);created.append(self);self.display=None
        def call(self,name,*args,**kwargs):
            if name=='BindWindow':self.display=args[1]
            if name=='Capture' and self.display=='dx':raise RuntimeError('no image')
            return super().call(name,*args,**kwargs)
    context=ExecutionContext(services={'background_windows':Windows,'background_transport':NoImage})
    try:
        bind_background(context,{'绑定等待':0})
        assert current_backend(context).binding_profile=='DX2'
        assert len(created)==1 and not created[0].closed
        assert [a[1] for n,a in created[0].calls if n=='BindWindow']==['dx','dx2']
    finally:close_background(context)
    assert created[0].closed


def test_locked_helper_cleanup_does_not_interrupt_execution():
    import tempfile
    from pathlib import Path
    from types import SimpleNamespace
    from background_runtime import release_host_directory
    with tempfile.TemporaryDirectory(prefix='anclicker-dm-host-') as folder:
        directory=SimpleNamespace(name=folder,cleanup=Mock(side_effect=PermissionError('mapped helper')))
        with patch('background_runtime.threading.Thread') as thread:
            release_host_directory(directory)
            thread.return_value.start.assert_called_once()
        directory.cleanup.assert_called_once()
        import background_runtime
        background_runtime._pending_host_cleanup.discard(Path(folder).resolve())
        background_runtime._cleanup_running=False


@pytest.mark.parametrize('type_id', ['绑定选择窗口', '解除后台绑定'])
def test_binding_state_forms_omit_redundant_template_controls_but_preserve_projects(app, type_id):
    editor = get_instruction_spec(type_id).create_editor()
    try:
        assert editor.repeat_count.isHidden() and editor.ui.repeatLabel.isHidden()
        assert editor.test_button.isHidden() == (type_id != '绑定选择窗口')
        assert not editor.error_policy.isHidden() and not editor.note.isHidden()
        assert editor.get_draft().repeat_count == 1
        if type_id == '解除后台绑定':
            assert editor.ui.parameterGroupBox.isHidden()
            assert editor.get_draft().parameters == {}
        # Old repeat settings remain explicit and round-trip unchanged.
        editor.load_draft(InstructionDraft(type_id, {}, repeat_count=3,
                                          error_policy='自动跳过', note='旧项目'))
        assert not editor.repeat_count.isHidden()
        restored = editor.get_draft()
        assert (restored.repeat_count, restored.error_policy, restored.note) == (3, '自动跳过', '旧项目')
        editor.repeat_count.setValue(1)
        assert editor.repeat_count.isHidden() and editor.get_draft().repeat_count == 1
    finally:
        editor.deleteLater()


def test_preset_hides_managed_modes_and_custom_exposes_them(app):
    from background_binding import MODE_KEYS
    editor = get_instruction_spec('绑定选择窗口').create_editor()
    try:
        for key in MODE_KEYS:
            assert editor._controls[key].isHidden()
        editor._controls['绑定方案'].setCurrentText(CUSTOM)
        for key in MODE_KEYS:
            assert not editor._controls[key].isHidden() and editor._controls[key].isEnabled()
        editor._controls['图像模式'].setCurrentText('gdi2')
        assert editor.get_draft().parameters['图像模式'] == 'gdi2'
        editor._controls['绑定方案'].setCurrentText('DX2')
        assert editor._controls['图像模式'].isHidden()
        assert editor.get_draft().parameters['图像模式'] == 'dx2'
    finally:
        editor.deleteLater()


def test_background_operations_only_show_applicable_arguments_and_help(app):
    from background_catalog import GROUPS
    for group in GROUPS:
        editor = get_instruction_spec(group).create_editor()
        try:
            assert editor.test_button.isHidden()
            assert editor._controls['参数'].isHidden() and editor.ui.label_1.isHidden()
            assert not editor.repeat_count.isHidden()
            assert not editor._controls['变量'].isHidden()
            editor.repeat_count.setValue(2)
            assert editor.get_draft().repeat_count == 2
        finally:
            editor.deleteLater()
    editor = get_instruction_spec('后台图色操作').create_editor()
    try:
        editor._controls['接口'].setCurrentText(label('FindPic'))
        assert '图片偏色' in editor.helpLabel.text() and 'HSV' not in editor.helpLabel.text()
        editor._controls['接口'].setCurrentText(label('FindColor'))
        assert 'HSV' in editor.helpLabel.text()
        editor._controls['接口'].setCurrentText(label('RGB2BGR'))
        assert '坐标' not in editor.helpLabel.text() and 'HSV' not in editor.helpLabel.text()
    finally:
        editor.deleteLater()
    editor = get_instruction_spec('后台键鼠操作').create_editor()
    try:
        editor._controls['接口'].setCurrentText(label('LeftClick'))
        assert editor.argumentBody.isHidden() and editor._arguments == {}
        assert '无需额外参数' in editor.helpLabel.text()
        editor._controls['接口'].setCurrentText(label('MoveTo'))
        assert not editor.argumentBody.isHidden() and set(editor._arguments) == {'x', 'y'}
    finally:
        editor.deleteLater()
