import sys,json
from pathlib import Path
sys.path.insert(0,str(Path(__file__).resolve().parents[1]))
from unittest.mock import Mock
from anclicker.platform.qt_compat.QtWidgets import QApplication
from anclicker.domain.instructions import ExecutionContext,CommandRecord
from anclicker.instructions.registry import get_instruction_spec
app=QApplication([]);spec=get_instruction_spec('窗口位置与大小')
e=spec.create_editor();e.target={'窗口句柄':'12'}
for op in ('设置位置和大小','仅移动位置','仅调整大小','记录位置和大小','恢复位置和大小'):
 e.operation.setCurrentText(op);d=e.get_draft();e.load_draft(d);assert e.get_draft().parameters==d.parameters
 assert e.record.isHidden()==(op not in ('记录位置和大小','恢复位置和大小'))
e.close()
w=Mock();w.resolve.side_effect=lambda target:target
w.gui.GetWindowPlacement.return_value=(0,3,(0,0),(0,0),(10,20,810,620))
w.gui.GetWindowRect.return_value=(10,20,810,620);w.gui.GetWindowLong.return_value=8
w.gui.IsIconic.return_value=False;w.gui.IsZoomed.return_value=False
c=ExecutionContext(services={'background_windows':lambda:w});executor=spec.create_executor()
def run(op,**kw):return executor.execute_once(c,CommandRecord(None,spec.type_id,dict({'窗口':{'窗口句柄':'12'},'操作':op},**kw)))
run('记录位置和大小');c.variables=json.loads(json.dumps(c.variables))
run('恢复位置和大小')
w.gui.SetWindowPlacement.assert_called_with(12,(0,3,(0,0),(0,0),(10,20,810,620)))
w.gui.SetWindowPos.assert_called_with(12,-1,0,0,0,0,19)
run('仅移动位置',X=-500,Y=10);w.gui.SetWindowPos.assert_called_with(12,0,-500,10,0,0,21)
run('仅调整大小',宽度=900,高度=700);w.gui.SetWindowPos.assert_called_with(12,0,0,0,900,700,22)
w.gui.SetWindowPos.reset_mock()
try:run('仅调整大小',宽度=0);raise AssertionError('zero width')
except ValueError:pass
w.gui.SetWindowPos.assert_not_called()
try:run('恢复位置和大小',记录名称='missing');raise AssertionError('missing record')
except ValueError:pass
c.variables['窗口位置记录']['窗口']['窗口句柄']='99'
try:run('恢复位置和大小');raise AssertionError('wrong window')
except ValueError:pass
print('PASS: five operation settings, JSON record roundtrip, placement/topmost restore, move/size flags, invalid and wrong-window rejection')
