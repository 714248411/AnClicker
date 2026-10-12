from instructions.common import FieldSpec
from instructions.common.rpa_instruction import RpaInstructionEditor, RpaInstructionExecutor
from importlib import import_module
Ui_InstructionEditor = import_module('.提取文本到表格_ui', __package__).Ui_InstructionEditor

class InstructionEditor(RpaInstructionEditor):
    TYPE_ID = '提取文本到表格'
    DISPLAY_NAME = '提取文本到表格'
    COMMAND_ID = 'extractTextToTable'
    UI_CLASS = Ui_InstructionEditor
    FIELDS = (
        FieldSpec('selector', '元素定位(要提取哪些元素的文本)', 'text', '', choices=(), minimum=0),
        FieldSpec('anchor', '锚点元素(可选，多个用;分隔)', 'text', '', choices=(), minimum=0),
        FieldSpec('anchorRel', '目标相对锚点的方位', 'choice', '下方', choices=('下方', '上方', '右侧', '左侧', '内部', '相邻'), minimum=0),
        FieldSpec('by', '定位方式', 'choice', '智能匹配', choices=('CSS选择器', 'XPath', '文本内容', '智能匹配', '锚点定位'), minimum=0),
        FieldSpec('all', '提取数量', 'choice', '全部匹配', choices=('单个', '全部匹配'), minimum=0),
        FieldSpec('filter', '内容过滤(选一个，或直接填 2-3 表示取第2~3个字符)', 'text', '文本与数字', choices=(), minimum=0),
        FieldSpec('toPath', '写到哪个表格(可拖文件进来，留空=新建到桌面)', 'text', '', choices=(), minimum=0),
        FieldSpec('toSheet', '工作表名(留空=第一个表)', 'text', '', choices=(), minimum=0),
        FieldSpec('toCell', '从哪个单元格开始写(如 A1、B2)', 'text', 'A1', choices=(), minimum=0),
        FieldSpec('save', '保存方式', 'choice', '保存', choices=('保存', '另存为'), minimum=0),
    )

class InstructionExecutor(RpaInstructionExecutor):
    TYPE_ID = '提取文本到表格'
    COMMAND_ID = 'extractTextToTable'
