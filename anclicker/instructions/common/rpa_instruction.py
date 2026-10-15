"""Instruction execution implementation."""
from __future__ import annotations
from anclicker.instructions.common import actions
from anclicker.platform.rpa_bridge import get_bridge
from anclicker.platform.rpa_bridge import ROOT
import json
from anclicker.instructions.common import InstructionExecutorBase
CATALOG = {item['id']: item for item in json.loads((ROOT / 'integrations/yingdao/commands.json').read_text(encoding='utf-8'))}

class RpaInstructionExecutor(InstructionExecutorBase):
    COMMAND_ID = ''

    def execute_once(self, context, command):
        (delegated, result) = actions.delegated(context, self.TYPE_ID, command)
        if delegated:
            return result
        definition = CATALOG[self.COMMAND_ID]
        parameters = {p['key']: p.get('default', '') for p in definition['params']}
        parameters.update(command.parameters)
        parameters = {k: actions.substitute_variables(context, v) if isinstance(v, str) and k not in {'varName', 'data'} else v for (k, v) in parameters.items()}
        response = get_bridge().execute({'id': self.COMMAND_ID, 'name': definition['name'], 'params': parameters}, context.variables, context=context)
        context.variables.update(response.get('variables', {}))
        result = response.get('result')
        if self.COMMAND_ID == 'clickXY' and parameters.get('pickOnly'):
            if not isinstance(result, dict):
                raise RuntimeError('未收到网页取点结果，请重新取点')
            context.set_variable('网页取点结果', result)
        if self.COMMAND_ID == 'pickElement':
            context.variables.pop('网页元素', None)
            context.variables.pop('网页元素详情', None)
            if not isinstance(result, dict):
                raise RuntimeError('未收到网页元素信息，请重新拾取')
            if result.get('error'):
                raise RuntimeError(str(result['error']))
            context.set_variable('网页元素详情', result)
            if result.get('canceled'):
                context.emit('拾取元素：已取消')
                return result
            if not result.get('css'):
                raise RuntimeError('拾取结果缺少定位信息，请重新拾取')
            context.set_variable('网页元素', result['css'])
        context.emit(definition['name'] + '：完成')
        return result
