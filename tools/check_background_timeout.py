import sys
from pathlib import Path
from unittest.mock import patch
from types import SimpleNamespace
sys.path.insert(0,str(Path(__file__).resolve().parents[1]))
from anclicker.instructions.common import background_web as module
from anclicker.domain.instructions import CommandRecord, ExecutionContext
p={'key':'自定义','customKey':'a'*1000,'interval':.5,'times':2}
assert module.execution_timeout('backgroundKey',p)>999.5
assert module.execution_timeout('backgroundClicks',{'points':'1,2;3,4','interval':300})>300
assert module.execution_timeout('backgroundClick',{})==180
for v in [float('nan'),float('inf'),-1,'invalid']:
 assert module.execution_timeout('backgroundKey',dict(p,interval=v))==180
class Executor(module.BackgroundWebExecutor):TYPE_ID='后台网页按键';COMMAND_ID='backgroundKey'
with patch.object(module,'get_bridge') as get,patch.object(module.actions,'delegated',return_value=(False,None)):
 get.return_value.execute.return_value={'result':'ok'}
 assert Executor().execute_once(ExecutionContext(),CommandRecord(None,'后台网页按键',p))=='ok'
 assert get.return_value.execute.call_args.kwargs['timeout']>999.5
print('PASS long sequence/point timeout allowance, invalid values and executor forwarding')
