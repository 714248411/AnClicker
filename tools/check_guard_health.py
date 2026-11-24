"""Guard migration checks with synthetic pixels and injected input."""
import os,sys,json,tempfile,time,threading
from pathlib import Path
sys.path.insert(0,str(Path(__file__).resolve().parents[1]));os.environ['QT_QPA_PLATFORM']='windows'
import numpy as np
from types import SimpleNamespace
from anclicker.domain.instructions import ExecutionContext,InstructionDraft
from anclicker.storage.database import DatabaseOperation
from anclicker.execution.engine import ExecutionEngine
from anclicker.execution.services import ExecutionServices
from anclicker.platform.vision_tools.runtime import execute,validate,close_monitors
from anclicker.platform.vision_tools.guard_health import preview,rules_from,key_code
from anclicker.instructions.registry import get_instruction_spec
from anclicker.platform.qt_compat.QtWidgets import QApplication,QMainWindow
from anclicker.platform.qt_compat.QtCore import Qt,QTimer,QEvent
from anclicker.platform.qt_compat.QtGui import QFont,QKeyEvent
from anclicker.ui.instruction_editors.health_guard import RecordGuardKey
from anclicker.ui.settings_theme import apply_settings_theme
from anclicker.ui.theme import THEMES
app=QApplication([]);app.setFont(QFont('Microsoft YaHei',10))
def wait(predicate,seconds=3):
    end=time.monotonic()+seconds
    while not predicate() and time.monotonic()<end:app.processEvents();time.sleep(.01)
    assert predicate(),'timeout'
rows=[dict(enabled=True,pos='1,0',color='255,0,0',key='ctrl+1',source='屏幕',window='',hwnd='',tolerance=0),
      dict(enabled=True,pos='2,0',color='255,0,0',key='nummultiply',source='窗口',window='测试窗口',hwnd='123',tolerance=10),
      dict(enabled=False,pos='',color='',key='')]
params={'检测方式':'守护取点检测','检测规则':json.dumps(rows),'监控名':'守护','连续次数':1,'间隔':.05,'冷却':.1}
assert key_code('nummultiply')==106 and key_code('xbutton2')==6
with tempfile.TemporaryDirectory() as temporary:
    db=DatabaseOperation(str(Path(temporary)/'test.db'));logs=[];inputs=[];pixels={1:(255,0,0),2:(0,0,0)}
    def capture(p):
        x=int(p['区域'].split(',')[0]);rgb=pixels[x]
        return np.array([[rgb[::-1]]],np.uint8),(x,0),123 if p['截图来源']=='窗口' else None
    context=ExecutionContext(services={'离线视觉截图':capture,'离线视觉输入':lambda *args:inputs.append(args)},output=logs.append)
    engine=ExecutionEngine(ExecutionServices(db));engine._active_context=context;engine._prepare_context(context)
    p=validate('多线程血量判断',params)
    result=preview(p,context);assert result['1']['触发'] is False and result['2']['触发'] is True and not inputs
    execute('多线程血量判断',params,context)
    wait(lambda:len(inputs)>=2);assert all(item[0]['按键']=='nummultiply' and item[2]==123 for item in inputs)
    engine.pause();time.sleep(.12);count=len(inputs);time.sleep(.15);assert len(inputs)==count
    engine.resume();wait(lambda:len(inputs)>count)
    close_monitors(context);count=len(inputs);time.sleep(.1);assert len(inputs)==count
    pixels[2]=(250,0,0);assert not preview(p,context)['2']['触发']
    assert len(rules_from(json.dumps(rows)))==3
    print('PASS enabled rows, exact/tolerant color comparison, window routing, numpad/side keys, pause/resume/stop, no-input preview')
    # Failure on one row must not stop the remaining rules or flood logs.
    pixels[2]=(0,0,0)
    def partial_capture(parameters):
        if parameters['区域'].startswith('1,'):raise RuntimeError('synthetic capture failure')
        return capture(parameters)
    context.services=dict(context.services,离线视觉截图=partial_capture)
    inputs.clear();execute('多线程血量判断',params,context);wait(lambda:len(inputs)>=3);close_monitors(context)
    assert sum('synthetic capture failure' in line for line in logs)==1
    print('PASS per-rule failure isolation and repeated-error suppression')
    spec=get_instruction_spec('多线程血量判断');editor=spec.create_editor(context=ExecutionContext(metadata={'database':db}))
    assert editor._controls['检测方式'].currentText()=='守护取点检测'
    assert not hasattr(editor,'guard_enabled')
    assert editor.table.cellWidget(0,3).text()=='取色' and editor.table.cellWidget(0,5).text()=='录键'
    assert editor.get_draft().parameters['守护启用']=='关闭'
    editor.remove_rule()
    for row in rows:editor.add_rule(row)
    before=[editor.rule(i) for i in range(editor.table.rowCount())]
    editor.fold_button.click();assert editor.table.isHidden()
    editor.fold_button.click();assert not editor.table.isHidden()
    editor.advanced_button.click();assert not editor.table.isColumnHidden(6) and not editor.table.isColumnHidden(8)
    editor.advanced_button.click();assert editor.table.isColumnHidden(6) and editor.table.isColumnHidden(8)
    assert [editor.rule(i) for i in range(editor.table.rowCount())]==before
    assert editor.rule(1)['window']=='测试窗口' and editor.rule(1)['hwnd']=='123'
    draft=editor.get_draft();restored=spec.create_editor(draft=draft,context=ExecutionContext(metadata={'database':db}))
    assert rules_from(restored.get_draft().parameters['检测规则'])==rules_from(draft.parameters['检测规则'])
    restored._controls['操作'].setCurrentText('停止监控');assert restored.guard_panel.isHidden();restored.get_draft()
    old=spec.create_editor(draft=InstructionDraft('多线程血量判断',{'区域':'0,0,100,10'}),context=ExecutionContext(metadata={'database':db}))
    assert old._controls['检测方式'].currentText()=='血量百分比' and old.guard_panel.isHidden();old.get_draft();old.close()
    record=RecordGuardKey();record.keyPressEvent(QKeyEvent(QEvent.KeyPress,Qt.Key_K,Qt.ControlModifier|Qt.ShiftModifier,'K'))
    assert record.value=='ctrl+shift+k'
    record=RecordGuardKey();record.keyPressEvent(QKeyEvent(QEvent.KeyPress,Qt.Key_Asterisk,Qt.KeypadModifier,'*'))
    assert record.value=='nummultiply';record.close()
    print('PASS full rule save/reopen, disabled rows retained, old percentage settings preserved, combo/numpad recording')
    # Take-point UI writes both coordinates and sampled color, without clicking the target.
    from anclicker.execution import actions
    from anclicker.platform.background_capture import BackgroundCaptureDialog
    from PIL import Image,ImageGrab
    import ctypes
    original_grab=ImageGrab.grab;original_exec=BackgroundCaptureDialog.exec
    ImageGrab.grab=lambda **kwargs:Image.new('RGB',(64,48),(12,34,56))
    def select_point(dialog):dialog.canvas.point=(8,5);return dialog.Accepted
    BackgroundCaptureDialog.exec=select_point
    try:
        editor.setAttribute(Qt.WA_DontShowOnScreen,True);editor.show();app.processEvents()
        editor.pick_rule(editor.table.cellWidget(0,3));wait(lambda:editor._job is None)
        expected=f'{8+ctypes.windll.user32.GetSystemMetrics(76)},{5+ctypes.windll.user32.GetSystemMetrics(77)}'
        assert editor.table.cellWidget(0,1).text()==expected and editor.table.cellWidget(0,2).text()=='12,34,56'
    finally:ImageGrab.grab=original_grab;BackgroundCaptureDialog.exec=original_exec
    editor.table.setRowCount(0)
    for row in rows:editor.add_rule(row)
    print('PASS actual take-point dialog result populates coordinate and color together')
    host=QMainWindow();host.view_workspace=SimpleNamespace(THEMES=THEMES,theme_mode='light')
    out=Path('artifacts/validation/guard-health');out.mkdir(parents=True,exist_ok=True)
    for mode in ('light','dark'):
        host.view_workspace.theme_mode=mode;apply_settings_theme(editor,host);editor.setAttribute(Qt.WA_DontShowOnScreen,True);editor.show();app.processEvents()
        editor.grab().save(str(out/(mode+'.png')));editor.hide()
    editor.show();app.processEvents()
    from anclicker.ui.adaptive_panels import AdaptivePanelSizer
    editor._panel_scaler=AdaptivePanelSizer(editor,editor,600,reference_height=420,base_pixels=13)
    for pixels in (14,9,18,13):
        editor._panel_scaler.expanded_pixels=pixels
        editor._panel_scaler.last_size=None
        editor._panel_scaler.apply();app.processEvents()
        assert editor.fold_button.height()>=editor.fold_button.sizeHint().height()
        app.processEvents();app.processEvents()
        assert editor.guard_hint.y()>=editor.table.geometry().bottom()
        assert editor.table.height()>=sum(editor.table.rowHeight(i) for i in range(3))
    editor.grab().save(str(out/'scaled.png'))
    editor.resize(720,540);editor.show();app.processEvents()
    assert editor.test_button.mapTo(editor,editor.test_button.rect().bottomRight()).y()<editor.height()
    editor.grab().save(str(out/'compact.png'));editor.hide()
    # Background capture cannot block the GUI or resurrect a closed editor.
    gate=threading.Event();callbacks=[];ticks=[]
    timer=QTimer();timer.setInterval(10);timer.timeout.connect(lambda:ticks.append(1));timer.start()
    editor.start_job(lambda:gate.wait(2),lambda value:callbacks.append(value));wait(lambda:len(ticks)>5)
    editor.close();gate.set();end=time.monotonic()+.2
    while time.monotonic()<end:app.processEvents();time.sleep(.01)
    assert not callbacks and not editor.isVisible();timer.stop();restored.close()
    print('PASS asynchronous capture keeps GUI responsive; closing prevents popup resurrection; light/dark render')
print('PASS full guard health suite')
