"""Client-pixel capture, recrop and real executor coordinate regressions."""
from types import SimpleNamespace as NS
from unittest.mock import Mock, patch
import json
import numpy as np
import pytest
from PIL import Image
from qt_compat.QtCore import QPoint, QPointF, QRect, QTimer, QCoreApplication, QEvent, Qt
from qt_compat.QtWidgets import QApplication, QDialog, QDialogButtonBox
from qt_compat.QtTest import QTest
from instructions.models import ExecutionContext, InstructionDraft, CommandRecord
from instructions.registry import get_instruction_spec
from background_capture import (CaptureCanvas, BackgroundCaptureDialog, CaptureSelection,
    capture_window, select_background, binding_parameters, isValid)
from background_capture_context import previous_binding
from background_runtime import bind_background, close_background, current_backend
from background_catalog import label
from test.test_background_runtime import Windows, Transport


def dispose(widget):
    if isValid(widget):
        widget.deleteLater()
        QCoreApplication.sendPostedEvents(widget, QEvent.DeferredDelete)


def context(parameters=None):
    return ExecutionContext(services={'background_windows': Windows, 'background_transport': Transport},
        metadata={'previous_background_binding': lambda: parameters if parameters is not None else {'绑定等待': 0}})


def editor(type_id='坐标点击', ctx=None, params=None):
    return get_instruction_spec(type_id).create_editor(context=ctx or context(),
        draft=InstructionDraft(type_id, params or {}))


def frame():
    return Image.fromarray(np.random.default_rng(45).integers(0,256,(150,200,3),dtype=np.uint8))


def logical(canvas, x, y):
    r = canvas.image_rect()
    return QPointF(r.x()+(x-canvas.view.x()+.5)*r.width()/canvas.view.width(),
                   r.y()+(y-canvas.view.y()+.5)*r.height()/canvas.view.height())


@pytest.mark.parametrize('size', [(300,200),(900,650),(1300,400)])
def test_scaled_letterboxed_preview_maps_exact_original_pixels(size):
    canvas = CaptureCanvas(frame())
    try:
        canvas.resize(*size)
        for x,y in [(0,0),(199,149),(10,20),(156,121)]:
            assert canvas.client_point(logical(canvas,x,y)) == (x,y)
        assert canvas.client_point(QPointF(0,0)) is None
        canvas.selection = QRect(31,27,91,63)
        canvas.crop_view()
        assert canvas.client_point(logical(canvas,50,41)) == (50,41)
        canvas.selection = QRect(45,39,40,25)
        canvas.crop_view()
        assert canvas.client_point(logical(canvas,68,51)) == (68,51)
        canvas.reset_view()
        assert canvas.client_point(logical(canvas,68,51)) == (68,51)
    finally:
        dispose(canvas)


def test_real_drag_recrop_keeps_native_pixels_and_absolute_origin(tmp_path):
    image = frame()
    dialog = BackgroundCaptureDialog(image)
    try:
        dialog.show(); QApplication.processEvents()
        canvas = dialog.canvas
        def drag(a,b):
            # Event.position supplies logical Qt coordinates, including fractional DPI.
            event = lambda p: NS(button=lambda:Qt.LeftButton, position=lambda:logical(canvas,*p))
            canvas.mousePressEvent(event(a));canvas.mouseReleaseEvent(event(b))
        drag((100,90),(31,27))
        dialog.crop_button.click()
        assert canvas.view == QRect(31,27,70,64)
        drag((48,42),(68,61))
        result = canvas.result()
        assert result.region == (48,42,21,20)
        assert result.point == (58,52)
        assert result.color == image.getpixel((58,52))
        path = tmp_path/'crop.png';result.save_selection(path)
        with Image.open(path) as saved:
            assert saved.tobytes() == image.crop((48,42,69,62)).tobytes()
        dialog.buttons.button(QDialogButtonBox.Ok).click()
        assert dialog.result() == QDialog.Accepted
    finally:
        dispose(dialog)


def snapshot(types, edges):
    commands = [NS(id=i+1,type_id=t,parameters={'窗口句柄':str(i+1)},order=i) for i,t in enumerate(types)]
    return NS(commands=commands, nodes=[NS(node_id=str(c.id),command_id=c.id) for c in commands]+[NS(node_id='start',command_id=None)],
              edges=[NS(source=str(a),target=str(b)) for a,b in edges])


def test_binding_resolution_respects_flow_and_unbind():
    s = snapshot(['绑定选择窗口','坐标点击','解除后台绑定','坐标点击'], [('start',1),(1,2),(2,3),(3,4)])
    assert previous_binding(s,2) == {'窗口句柄':'1'}
    assert previous_binding(s,4) is None
    assert previous_binding(s) is None
    s.edges.append(NS(source='2',target='2'))
    assert previous_binding(s,2) == {'窗口句柄':'1'}


@pytest.mark.parametrize('edges', [[('start',1),(1,3),(2,3)],[(1,3),('start',3)]])
def test_ambiguous_branch_never_guesses_window(edges):
    s = snapshot(['绑定选择窗口','绑定选择窗口','坐标点击'],edges)
    with pytest.raises(ValueError,match='不同的后台绑定'):
        previous_binding(s,3)


def test_capture_uses_own_worker_session_and_always_releases_binding():
    created=[]
    class Tracked(Transport):
        def __init__(self,ctx):
            super().__init__(ctx); created.append(self)
    ctx=context();ctx.services=dict(ctx.services,background_transport=Tracked)
    owner=editor(ctx=ctx)
    try:
        image=capture_window(owner,{'绑定等待':0})
        assert image.size==(200,150)
        assert len(created)==1 and created[0].closed
        assert ('UnBindWindow',()) in created[0].calls
        assert not any(n in ('MoveTo','LeftClick') for n,a in created[0].calls)
        assert current_backend(ctx) is None
    finally:dispose(owner)


@pytest.mark.parametrize('failure',['capture','resize'])
def test_capture_failure_cleans_up_and_never_returns_wrong_size(failure):
    created=[]
    class Bad(Transport):
        def __init__(self,ctx):super().__init__(ctx);created.append(self)
        def call(self,name,*args,**kw):
            if name=='Capture':
                if failure=='capture':raise RuntimeError('capture failed')
                Image.new('RGB',(199,150)).save(args[4]);return 1
            return super().call(name,*args,**kw)
    ctx=context();ctx.services=dict(ctx.services,background_transport=Bad)
    owner=editor(ctx=ctx)
    try:
        with pytest.raises(RuntimeError):capture_window(owner,{'绑定等待':0,'绑定方案':'GDI 兼容'})
        assert created and all(t.closed for t in created)
    finally:dispose(owner)


def test_input_only_binding_requires_capture_and_does_not_fall_back():
    owner=editor(ctx=context({'启用截图':False}))
    try:
        with patch('background_capture.capture_window',wraps=capture_window) as capture, patch('instructions.common.editor.QMessageBox.warning') as warning, patch('instructions.common.editor._PointSelectionDialog') as foreground:
            owner._select_screen_point('坐标',owner._controls['坐标'])
        assert capture.called and warning.called
        foreground.assert_not_called()
    finally:dispose(owner)


@pytest.mark.parametrize('type_id',['坐标点击','移动鼠标','颜色判断'])
def test_selected_client_coordinate_roundtrip_to_real_background_executor(type_id):
    ctx=context();owner=editor(type_id,ctx,{'类型':'指定坐标'} if type_id=='移动鼠标' else {})
    selection=CaptureSelection(Image.new('RGB',(1,1)),(73,49,1,1),(73,49),(17,34,51))
    try:
        with patch('background_capture.select_background',return_value=selection):
            owner._select_screen_point('坐标',owner._controls['坐标'])
        draft=owner.get_draft()
        assert draft.parameters['坐标']=='73,49'
        bind_background(ctx,{'绑定等待':0})
        backend=current_backend(ctx)
        get_instruction_spec(type_id).create_executor().execute(ctx,CommandRecord(1,type_id,draft.parameters))
        assert ('GetColor',(73,49)) in backend.transport.calls if type_id=='颜色判断' else ('MoveTo',(73,49)) in backend.transport.calls
        if type_id=='坐标点击':assert ('LeftClick',()) in backend.transport.calls
    finally:close_background(ctx);dispose(owner)


def test_background_move_editor_capture_updates_visible_and_raw_coordinates():
    ctx=context();owner=editor('后台键鼠操作',ctx,{'接口':label('MoveTo'),'参数':'{}'})
    try:
        selection=CaptureSelection(Image.new('RGB',(1,1)),(74,50,1,1),(74,50),(0,0,0))
        with patch('background_capture.select_background',return_value=selection):
            owner._capture_argument(owner._argument_widgets['坐标'])
        draft=owner.get_draft()
        assert json.loads(draft.parameters['参数']) == {'x':'74','y':'50'}
        bind_background(ctx,{'绑定等待':0}); backend=current_backend(ctx)
        get_instruction_spec(draft.type_id).create_executor().execute(ctx,CommandRecord(1,draft.type_id,draft.parameters))
        assert ('MoveTo',(74,50)) in backend.transport.calls
    finally:close_background(ctx);dispose(owner)


def test_cropped_template_matches_window_coordinates_without_double_offset(tmp_path):
    image=frame();path=tmp_path/'target.png'
    image.crop((48,42,69,62)).save(path)
    class Capture(Transport):
        def call(self,name,*args,**kw):
            if name=='Capture':
                self.calls.append((name,args));image.crop(args[:4]).save(args[4]);return 1
            return super().call(name,*args,**kw)
    ctx=ExecutionContext(services={'background_windows':Windows,'background_transport':Capture})
    try:
        bind_background(ctx,{'绑定等待':0});backend=current_backend(ctx)
        command=CommandRecord(1,'图像点击',{'图像路径':str(path),'精度':.99,'动作':'左键单击','异常':'0','区域':'31,27,100,90','点击位置':'3,-2'})
        with patch('pyautogui.click',side_effect=AssertionError('foreground click')):
            result=get_instruction_spec('图像点击').create_executor().execute(ctx,command)
        assert result==(61,50)
        assert ('MoveTo',(61,50)) in backend.transport.calls
        assert ('LeftClick',()) in backend.transport.calls
    finally:close_background(ctx)


@pytest.mark.parametrize('outcome',['accept','cancel','delete'])
def test_modal_preview_lifecycle_and_guard_restore(outcome):
    owner=editor(); owner.show(); QApplication.processEvents()
    before=owner._controls['坐标'].text()
    seen=[]
    def interact():
        dialogs=[d for d in QApplication.topLevelWidgets() if isinstance(d,BackgroundCaptureDialog)]
        if not dialogs:return
        dialog=dialogs[0];seen.append(dialog)
        if outcome=='delete':dispose(owner)
        elif outcome=='cancel':dialog.reject()
        else:
            dialog.canvas.point=(10,20);dialog.canvas.selection=QRect(10,20,1,1);dialog.accept()
    timer=QTimer();timer.timeout.connect(interact);timer.start(20)
    try:
        with patch('background_capture.capture_window',return_value=frame()):
            result=select_background(owner,{},'point')
        assert seen
        if outcome=='accept':assert result.point==(10,20)
        else:assert result is None
        if isValid(owner):
            assert not owner._background_capture_active and owner.ui.buttonBox.isEnabled()
            assert owner._controls['坐标'].text()==before
    finally:timer.stop();dispose(owner)


@pytest.mark.parametrize('capture',[True,False])
def test_image_editor_uses_bound_image_and_keeps_client_region(tmp_path,capture):
    from 数据库操作 import DatabaseOperation
    ctx=context();ctx.metadata['database']=DatabaseOperation(str(tmp_path/'image-editor.db'))
    ctx.metadata['database'].writes_to_resource_folder_path(str(tmp_path))
    remember=Mock();ctx.metadata['remember_capture']=remember
    owner=editor('图像点击',ctx)
    original=tmp_path/'original.png';frame().save(original);owner._set_image_path(original)
    image=frame().crop((48,42,69,62));selection=CaptureSelection(image,(48,42,21,20),(58,52),(17,34,51))
    try:
        with patch('background_capture.select_background',return_value=selection) as select, patch('instructions.common.image_click_editor.SmartCaptureDialog') as foreground:
            owner._select_screen(capture)
        select.assert_called_once();foreground.assert_not_called()
        if capture:
            saved=owner._controls['图像路径'].text()
            with Image.open(saved) as actual:assert actual.tobytes()==image.tobytes()
            remember.assert_called_once_with(saved)
        else:
            assert owner.ui.parameter_3.text()==str(selection.region)
            assert owner.region_group.isChecked()
            assert owner._controls['图像路径'].text()==str(original)
    finally:dispose(owner)


def test_binding_quick_capture_saves_crop_and_original_client_coordinates(tmp_path):
    owner=editor('绑定选择窗口',context(),{'窗口句柄':'123'})
    selection=CaptureSelection(frame().crop((48,42,69,62)),(48,42,21,20),(58,52),(1,2,3))
    try:
        with patch('background_capture.select_background',return_value=selection) as select, patch('functions.IMAGES_FOLDER',str(tmp_path)):
            owner.quickCaptureButton.click()
        assert select.call_args.args[1]['窗口句柄']=='123'
        assert '48,42,21,20' in owner.capture_result.text() and '58,52' in owner.capture_result.text()
        files=list(tmp_path.glob('*.png'));assert len(files)==1
        with Image.open(files[0]) as saved:assert saved.tobytes()==selection.image.tobytes()
    finally:dispose(owner)


def test_find_pic_quick_capture_saves_backend_compatible_bitmap(tmp_path):
    owner=editor('后台图色操作',context(),{'接口':label('FindPic'),'参数':'{}'})
    selection=CaptureSelection(frame().crop((48,42,69,62)),(48,42,21,20),(58,52),(1,2,3))
    try:
        with patch('background_capture.select_background',return_value=selection),patch('functions.IMAGES_FOLDER',str(tmp_path)):
            owner._capture_argument(image_control=owner._arguments['pic_name'])
        path=owner._arguments['pic_name'].text()
        with Image.open(path) as saved:assert saved.format=='BMP' and saved.tobytes()==selection.image.tobytes()
    finally:dispose(owner)


@pytest.mark.parametrize('action',['cancel','delete'])
def test_cancel_while_worker_is_binding_waits_for_cleanup_without_error(action):
    import time
    from instructions.common.test_runner import CancellableTestDialog
    created=[]
    class Slow(Transport):
        def __init__(self,ctx):super().__init__(ctx);created.append(self);self.context=ctx
        def call(self,name,*args,**kw):
            if name=='BindWindow':
                end=time.monotonic()+2
                while not self.context.stop_requested and time.monotonic()<end:time.sleep(.005)
            return super().call(name,*args,**kw)
    ctx=context();ctx.services=dict(ctx.services,background_transport=Slow);owner=editor(ctx=ctx)
    done=[]
    def cancel():
        if not created or done:return
        if action=='delete':dispose(owner)
        else:
            progress=next((w for w in QApplication.topLevelWidgets() if isinstance(w,CancellableTestDialog) and w.isVisible()),None)
            if progress is None:return
            progress.reject()
        done.append(True)
    timer=QTimer();timer.timeout.connect(cancel);timer.start(10)
    try:
        assert capture_window(owner,{'绑定等待':0}) is None
        assert done and created and all(t.closed for t in created)
    finally:timer.stop();dispose(owner)


def test_workspace_editor_context_resolves_the_connected_binding(tmp_path):
    from qt_compat.QtWidgets import QWidget
    from 数据库操作 import DatabaseOperation
    from instruction_workspace import InstructionWorkspace
    owner=QWidget();owner.db=DatabaseOperation(str(tmp_path/'workspace.db'))
    workspace=InstructionWorkspace(owner.db.db_path,owner)
    try:
        repo=workspace.repository
        bind=repo.add_command(InstructionDraft('绑定选择窗口',{'窗口句柄':'456'}),unconnected=True)
        click=repo.add_command(InstructionDraft('坐标点击',{'坐标':'0,0'}),unconnected=True)
        nodes={n.command_id:n.node_id for n in repo.snapshot().nodes}
        repo.connect_nodes('start',nodes[bind.id]);repo.connect_nodes(nodes[bind.id],nodes[click.id])
        ctx=workspace._editor_context(click.id)
        assert ctx.metadata['previous_background_binding']()=={'窗口句柄':'456'}
    finally:dispose(owner)


@pytest.mark.parametrize('theme',['light','dark'])
def test_preview_uses_workspace_theme(theme,tmp_path):
    from view_workspace import ViewWorkspace
    from settings_theme import apply_settings_theme
    from qt_compat.QtGui import QPalette
    # Use the same theme source as real settings dialogs, without a second main window.
    colors=ViewWorkspace.THEMES[theme]
    host=NS(view_workspace=NS(THEMES=ViewWorkspace.THEMES,theme_mode=theme))
    dialog=BackgroundCaptureDialog(frame())
    try:
        apply_settings_theme(dialog,host)
        dialog.show();QApplication.processEvents()
        assert dialog.canvas.palette().color(QPalette.Window).name()==colors['surface'].lower()
        assert dialog.canvas.palette().color(QPalette.WindowText).name()==colors['text'].lower()
        assert dialog.buttons.button(QDialogButtonBox.Ok).height()>=dialog.fontMetrics().height()
    finally:dispose(dialog)
