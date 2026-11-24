import os,sys,random,tempfile
from pathlib import Path
from unittest.mock import patch
sys.path.insert(0,str(Path(__file__).resolve().parents[1]))
os.environ['ANCLICKER_DATA_DIR']=tempfile.mkdtemp(prefix='human-mouse-')
os.environ['QT_QPA_PLATFORM']='offscreen'
from anclicker.app.paths import ensure_data_directories
ensure_data_directories()
from anclicker.execution.human_mouse import mouse_path
from anclicker.instructions.键鼠.移动鼠标.executor import InstructionExecutor
from anclicker.domain.instructions import ExecutionContext,CommandRecord,InstructionDraft
class Mouse:
    def __init__(self):self.xy=(100,100);self.points=[]
    def position(self):return self.xy
    def size(self):return (800,600)
    def moveTo(self,x,y,**kw):self.xy=(x,y);self.points.append((x,y))
for algorithm in ('wind','bezier'):
    for end in ((100,100),(101,100),(700,500),(-300,500)):
        points=mouse_path((100,100),end,algorithm,random.Random(7))
        assert points[-1]==end
        assert len(points)<=2001
    assert mouse_path((100,100),(700,500),algorithm,random.Random(7))!=mouse_path((100,100),(700,500),algorithm,random.Random(8))
for mode in ('模拟人1（WindMouse）','模拟人2（BezMouse）'):
    for direction,target in [('无',(500,300)),('→',(180,100)),('↑',(100,20))]:
        gui=Mouse();context=ExecutionContext()
        command=CommandRecord(1,'移动鼠标',{'类型':mode,'方向':direction,'距离':80,'坐标':'500,300','持续':0})
        with patch('anclicker.instructions.键鼠.移动鼠标.executor.actions.pyautogui_module',return_value=gui):
            assert InstructionExecutor().execute_once(context,command)==target
        assert gui.points[-1]==target
        assert all(0<=x<800 and 0<=y<600 for x,y in gui.points)
    gui=Mouse();context=ExecutionContext(stop_requested=True)
    with patch('anclicker.instructions.键鼠.移动鼠标.executor.actions.pyautogui_module',return_value=gui):
        InstructionExecutor().execute_once(context,command)
    assert not gui.points
from anclicker.platform.qt_compat import configure_application
configure_application()
from anclicker.platform.qt_compat.QtWidgets import QApplication
from anclicker.ui.instruction_editors.键鼠.移动鼠标 import InstructionEditor
app=QApplication([])
for mode in ('模拟人1（WindMouse）','模拟人2（BezMouse）'):
    editor=InstructionEditor()
    editor._controls['类型'].setCurrentText(mode)
    assert editor._controls['方向'].currentText()=='无'
    editor._controls['坐标'].setText('500,300')
    draft=editor.get_draft()
    restored=InstructionEditor(draft=draft)
    assert restored.get_draft().parameters['类型']==mode
    assert restored.get_draft().parameters['方向']=='无'
    restored.close();editor.close()
print('PASS bounded randomized paths, exact endpoints, directions, cancellation, editor modes and roundtrip')

editor=InstructionEditor()
assert editor.get_draft().parameters['类型']=='模拟人1（WindMouse）'
assert editor.get_draft().parameters['方向']=='无'
def check_visible(expected):
    for i,field in enumerate(editor.FIELDS):
        label=getattr(editor.ui,'parameterLabel_'+str(i))
        widget=getattr(editor.ui,'parameterContainer_'+str(i),editor._controls[field.key])
        assert (not label.isHidden())==(field.key in expected),field.key
        assert (not widget.isHidden())==(field.key in expected),field.key
check_visible({'类型','坐标','持续'})
assert editor._controls['持续'].text()=='0.5-1.5'
editor._controls['类型'].setCurrentText('模拟人2（BezMouse）')
editor._controls['方向'].setCurrentText('←')
check_visible({'类型','方向','距离','持续'})
editor._controls['距离'].setValue(123)
saved=editor.get_draft()
editor.load_draft(saved)
assert editor._controls['方向'].currentText()=='←'
assert editor._controls['距离'].value()==123
check_visible({'类型','方向','距离','持续'})
for mode,fields in [
    ('随机移动',{'类型','随机','持续'}),
    ('指定坐标',{'类型','坐标','持续'}),
    ('变量坐标',{'类型','变量','持续'}),
    ('直线移动',{'类型','方向','距离','持续'}),
    ('模拟人2（BezMouse）',{'类型','方向','坐标','持续'}),
]:
    editor._controls['类型'].setCurrentText(mode)
    check_visible(fields)
editor.load_draft(InstructionDraft(type_id='移动鼠标',parameters={}))
assert editor._controls['类型'].currentText()=='直线移动'
assert editor._controls['方向'].currentText()=='→'
check_visible({'类型','方向','距离','持续'})
editor.close()
print('PASS new defaults, all mode-specific rows, direction switching, saved settings, legacy defaults')

from anclicker.instructions.键鼠.移动鼠标.timing import duration_bounds
assert duration_bounds('0.5-1.5')==(0.5,1.5)
assert duration_bounds('1')==(1,1)
for invalid in ('-1','2-1','nan','inf','abc','3601'):
    try: duration_bounds(invalid)
    except ValueError: pass
    else: raise AssertionError(invalid)
editor=InstructionEditor()
form=editor.ui.parameterFormLayout
assert form.getWidgetPosition(editor._controls['类型'])[0] < form.getWidgetPosition(editor.ui.parameterContainer_4)[0] < form.getWidgetPosition(editor._controls['持续'])[0]
for value in ('0.5-1.5','1'):
    editor._controls['持续'].setText(value)
    draft=editor.get_draft()
    restored=InstructionEditor(draft=draft)
    assert restored._controls['持续'].text()==value
    restored.close()
    gui=Mouse()
    command=CommandRecord(1,'移动鼠标',draft.parameters)
    with patch('anclicker.instructions.键鼠.移动鼠标.executor.actions.pyautogui_module',return_value=gui), patch('anclicker.instructions.键鼠.移动鼠标.executor.random.uniform',return_value=0.8) as random_time, patch('anclicker.execution.human_mouse.move_human',return_value=(0,0)) as move:
        InstructionExecutor().execute_once(ExecutionContext(),command)
        assert move.call_args.args[3]==(0.8 if '-' in value else 1)
        assert random_time.call_count==(1 if '-' in value else 0)
editor.close()
print('PASS row order, duration validation, fixed/random duration execution and roundtrip')
