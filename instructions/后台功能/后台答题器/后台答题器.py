"""Local Word answers. The historical type ID is kept for saved workbooks."""
from instructions.common import FieldSpec, SchemaInstructionEditor, InstructionExecutorBase, actions
from .后台答题器_ui import Ui_InstructionEditor

class InstructionEditor(SchemaInstructionEditor):
    TYPE_ID = '后台答题器'
    DISPLAY_NAME = '本地Word答题器'
    UI_CLASS = Ui_InstructionEditor
    FIELDS = (
        FieldSpec('题库路径', 'Word 题库 (.docx)', 'path', '', required=True),
        FieldSpec('题目来源', '题目来源', 'choice', '输入题目', ('输入题目', '最近OCR文字', '变量')),
        FieldSpec('题目', '题目内容 / 变量名', 'text', ''),
        FieldSpec('匹配方式', '匹配方式', 'choice', '精准', ('精准', '包含', '模糊')),
        FieldSpec('相似度', '模糊匹配相似度', 'float', .85, minimum=.01, maximum=1),
        FieldSpec('未找到', '未找到答案', 'choice', '报错', ('报错', '返回空值')),
        FieldSpec('变量', '答案变量', 'text', '答案', required=True),
    )

    def __init__(self, parent=None, draft=None, context=None):
        super().__init__(parent, draft=draft, context=context)
        from qt_compat.QtWidgets import QLabel
        hint = QLabel('本地读取 .docx 题库，无需后台绑定。支持“题目/答案”两列表格，或“题目：…”与“答案：…”段落。答案保存到变量后供下一步使用。', self)
        hint.setWordWrap(True)
        self.ui.rootLayout.insertWidget(1, hint)

    def _run_auxiliary(self, key):
        if key == '题库路径':
            from qt_compat.QtWidgets import QFileDialog
            path, _ = QFileDialog.getOpenFileName(self, '选择本地 Word 题库', '', 'Word 文档 (*.docx)')
            if path:
                self._controls[key].setText(path)
            return
        super()._run_auxiliary(key)

class InstructionExecutor(InstructionExecutorBase):
    TYPE_ID = '后台答题器'
    CONSUMED_FIELDS = tuple(field.key for field in InstructionEditor.FIELDS)

    def execute_once(self, context, command):
        if command.type_id != self.TYPE_ID:
            raise ValueError('本地Word答题器收到不匹配的指令')
        handled, result = actions.delegated(context, self.TYPE_ID, command)
        if handled:
            return result
        from local_word_answers import load_bank, find_answer
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
            from instructions.models import ExecutionContext
            question = actions.substitute_variables(ExecutionContext(variables=source_variables), str(p.get('题目', '')))
        else:
            raise ValueError('请选择有效题目来源')
        path = actions.resolve_image_path({'图像路径': p['题库路径']}, context)
        result = find_answer(load_bank(path), question, p.get('匹配方式', '精准'), p.get('相似度', .85))
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
