from instructions.common import FieldSpec, SchemaInstructionEditor
from instructions.common.background_instruction import BackgroundMethodEditor, BackgroundExecutor, BindingEditor
from importlib import import_module
Ui_InstructionEditor = import_module('.后台汇编操作_ui', __package__).Ui_InstructionEditor

class InstructionEditor(BackgroundMethodEditor):
    TYPE_ID = DISPLAY_NAME = '后台汇编操作'
    UI_CLASS = Ui_InstructionEditor
    FIELDS = (
        FieldSpec(key='接口', label='操作', kind='choice', default='添加 MASM 语句 · AsmAdd', choices=('添加 MASM 语句 · AsmAdd', '清空 MASM 语句 · AsmClear', '执行 MASM · AsmCall', '执行 MASM 并指定参数 · AsmCallEx', 'MASM 转机器码 · Assemble', '机器码转 MASM · DisAssemble', '设置汇编执行超时 · AsmSetTimeout'), required=False, minimum=-1000000, maximum=1000000),
        FieldSpec(key='参数', label='接口参数', kind='multiline', default='{}', choices=(), required=False, minimum=-1000000, maximum=1000000),
        FieldSpec(key='变量', label='结果变量（可选）', kind='text', default='', choices=(), required=False, minimum=-1000000, maximum=1000000),
    )

class InstructionExecutor(BackgroundExecutor):
    TYPE_ID = '后台汇编操作'
