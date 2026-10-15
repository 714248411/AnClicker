"""Instruction execution implementation."""
from __future__ import annotations
from .schema import FIELDS
from anclicker.instructions.common import actions
from anclicker.instructions.common import InstructionExecutorBase

from anclicker._imports import DeferredImports as _DeferredImports

# Dependencies declared here retain their existing on-demand loading boundaries.
_module_imports = _DeferredImports(globals(), {
    'load_bank_find_answer': ('from', 'anclicker.execution.local_word_answers', ('load_bank', 'find_answer'), 0),
    'ExecutionContext': ('from', 'anclicker.domain.instructions', ('ExecutionContext',), 0),
})


class InstructionExecutor(InstructionExecutorBase):
    TYPE_ID = '后台答题器'
    CONSUMED_FIELDS = tuple((field.key for field in FIELDS))

    def execute_once(self, context, command):
        if command.type_id != self.TYPE_ID:
            raise ValueError('本地Word答题器收到不匹配的指令')
        (handled, result) = actions.delegated(context, self.TYPE_ID, command)
        if handled:
            return result
        load_bank, find_answer = _module_imports.load('load_bank_find_answer')
        p = command.parameters
        variable = str(p.get('变量', '答案')).strip()
        if not variable:
            raise ValueError('请设置答案变量')
        source_variables = dict(context.variables)
        context.set_variable(variable, '')
        context.set_variable(variable + '_详情', None)
        if not actions.wait_interruptibly(context, 0):
            return None
        if not p.get('题库路径'):
            raise ValueError('请重新配置本地 Word 题库路径；旧在线答题接口已停用')
        source = p.get('题目来源', '输入题目')
        if source == '最近OCR文字':
            question = context.metadata.get('last_ocr_text') or ''
        elif source == '变量':
            name = str(p.get('题目', '')).strip().removeprefix('{{').removesuffix('}}')
            if name not in source_variables:
                raise ValueError('题目变量不存在：' + name)
            question = source_variables[name]
        elif source == '输入题目':
            ExecutionContext = _module_imports.load('ExecutionContext')
            question = actions.substitute_variables(ExecutionContext(variables=source_variables), str(p.get('题目', '')))
        else:
            raise ValueError('请选择有效题目来源')
        path = actions.resolve_image_path({'图像路径': p['题库路径']}, context)
        result = find_answer(load_bank(path), question, p.get('匹配方式', '精准'), p.get('相似度', 0.85))
        if not actions.wait_interruptibly(context, 0):
            return None
        if result is None:
            if p.get('未找到', '报错') != '返回空值':
                raise ValueError('本地 Word 题库未找到匹配答案')
            return ''
        context.set_variable(variable, result['answer'])
        context.set_variable(variable + '_详情', result)
        context.emit('本地Word答题器：答案已写入变量 ' + variable)
        return result['answer']
