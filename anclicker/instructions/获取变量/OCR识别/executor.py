"""Instruction execution implementation."""
from __future__ import annotations
from anclicker.instructions.common import actions
import io
from anclicker.domain.instructions import ExecutionContext
from anclicker.domain.instructions import CommandRecord
from anclicker.instructions.common import InstructionExecutorBase

from anclicker._imports import DeferredImports as _DeferredImports

# Dependencies declared here retain their existing on-demand loading boundaries.
_module_imports = _DeferredImports(globals(), {
    'AipOcr': ('from', 'aip', ('AipOcr',), 0),
})


class InstructionExecutor(InstructionExecutorBase):
    TYPE_ID = 'OCR识别'

    def execute_once(self, context: ExecutionContext, command: CommandRecord):
        if command.type_id != self.TYPE_ID:
            raise ValueError(f'OCR识别执行器不能执行{command.type_id}')
        (delegated_, result_) = actions.delegated(context, self.TYPE_ID, command)
        if not delegated_:
            service_ = context.service('OCR')
            region_ = actions.region(actions.parameter(command.parameters, '区域'))
            if service_ is not None:
                result_ = service_(region=region_)
            else:
                result_ = self._recognize(context, region_)
        actions.store_variable(context, command.parameters, result_)
        context.emit(f'OCR识别：{result_}')
        return result_

    @staticmethod
    def _recognize(context: ExecutionContext, region_) -> str:
        database_ = getattr(getattr(context, 'runtime', None), 'database', None) or context.metadata.get('database')
        if database_ is None:
            raise RuntimeError('OCR识别缺少数据库配置上下文')
        client_info_ = database_.get_ocr_info()
        missing_ = [name_ for name_ in ('appId', 'apiKey', 'secretKey') if not client_info_.get(name_)]
        if missing_:
            raise RuntimeError(f"请先设置百度OCR参数：{', '.join(missing_)}")
        image_ = actions.pyautogui_module().screenshot(region=region_)
        image_bytes_ = io.BytesIO()
        image_.save(image_bytes_, format='PNG')
        AipOcr = _module_imports.load('AipOcr')
        client_ = AipOcr(client_info_['appId'], client_info_['apiKey'], client_info_['secretKey'])
        response_ = client_.basicGeneral(image_bytes_.getvalue())
        if response_.get('error_code'):
            raise RuntimeError(f"OCR识别失败：{response_.get('error_msg') or response_['error_code']}")
        return '\n'.join((str(item_.get('words', '')) for item_ in response_.get('words_result', [])))
