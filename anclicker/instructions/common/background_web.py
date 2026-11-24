"""CDP background web execution."""
from anclicker.instructions.common import InstructionExecutorBase, actions
from anclicker.platform.rpa_bridge import get_bridge
import math
class BackgroundWebExecutor(InstructionExecutorBase):
    COMMAND_ID = ''
    def execute_once(self, context, command):
        delegated, result = actions.delegated(context, self.TYPE_ID, command)
        if delegated: return result
        params = {k: actions.substitute_variables(context,v) if isinstance(v,str) else v for k,v in command.parameters.items()}
        response = get_bridge().execute({'id':self.COMMAND_ID,'params':params},context.variables,context=context, timeout=execution_timeout(self.COMMAND_ID, params))
        result = response.get('result')
        if params.get('pickOnly'):
            if not isinstance(result,dict): raise RuntimeError('未收到网页取点结果')
            context.set_variable('网页取点结果',result)
        else: context.emit(self.TYPE_ID+'：完成')
        return result


def execution_timeout(command_id, params):
    """Allow configured inter-key/point waits while the bridge keeps polling stop."""
    if params.get('pickOnly'):
        return 180
    try:
        interval = float(params.get('interval', .1 if command_id == 'backgroundKey' else 0))
        if not math.isfinite(interval) or not 0 <= interval <= 3600:
            return 180  # The engine reports invalid input.
        if command_id == 'backgroundKey':
            count = len(str(params.get('customKey') or '')) if params.get('key') == '自定义' else 1
            count = max(1, min(1000, count)) * max(1, min(20, int(params.get('times') or 1)))
        elif command_id == 'backgroundClicks':
            count = max(1, min(1000, len(str(params.get('points') or '').replace('；', ';').split(';'))))
        else:
            return 180
        return max(180, (count - 1) * interval + count * 2 + 180)
    except (TypeError, ValueError, OverflowError):
        return 180
