from instructions.common import FieldSpec
from instructions.common.rpa_instruction import RpaInstructionEditor, RpaInstructionExecutor
from importlib import import_module
Ui_InstructionEditor = import_module('.粘贴到单元格_ui', __package__).Ui_InstructionEditor

class InstructionEditor(RpaInstructionEditor):
    TYPE_ID = '粘贴到单元格'
    DISPLAY_NAME = '粘贴到单元格'
    COMMAND_ID = 'pasteToCell'
    UI_CLASS = Ui_InstructionEditor
    FIELDS = (
        FieldSpec('toPath', '写到哪个表格(可拖文件进来，留空=新建到桌面)', 'text', '', choices=(), minimum=0),
        FieldSpec('toSheet', '工作表名(留空=第一个表)', 'text', '', choices=(), minimum=0),
        FieldSpec('toCell', '从哪个单元格开始粘贴(如 A1、B2)', 'text', 'A1', choices=(), minimum=0),
        FieldSpec('save', '保存方式', 'choice', '保存', choices=('保存', '另存为'), minimum=0),
    )

class InstructionExecutor(RpaInstructionExecutor):
    TYPE_ID = '粘贴到单元格'
    COMMAND_ID = 'pasteToCell'
