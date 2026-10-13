from instructions.common import FieldSpec, SchemaInstructionEditor
from instructions.common.background_instruction import BackgroundMethodEditor, BackgroundExecutor, BindingEditor
from importlib import import_module
Ui_InstructionEditor = import_module('.后台文字识别_ui', __package__).Ui_InstructionEditor

class InstructionEditor(BackgroundMethodEditor):
    TYPE_ID = DISPLAY_NAME = '后台文字识别'
    UI_CLASS = Ui_InstructionEditor
    FIELDS = (
        FieldSpec(key='接口', label='操作', kind='choice', default='文字识别 · Ocr', choices=('文字识别 · Ocr', '文字识别及位置 · OcrEx', '识别图片文字 · OcrInFile', '查找文字 · FindStr', '查找全部文字位置 · FindStrEx', 'FindStrE', 'FindStrFast', 'FindStrFastEx', 'FindStrFastE', 'FindStrWithFont', 'FindStrWithFontE', 'FindStrWithFontEx', '识别词组 · GetWords', '无字库词组识别 · GetWordsNoDict', 'GetWordResultCount', 'GetWordResultPos', 'GetWordResultStr', 'GetResultCount', 'GetResultPos', 'SetExactOcr', 'SetMinRowGap', 'SetMinColGap', 'SetWordLineHeight', 'SetWordGap', 'SetRowGapNoDict', 'SetColGapNoDict', 'SetWordLineHeightNoDict', 'SetWordGapNoDict', 'FetchWord'), required=False, minimum=-1000000, maximum=1000000),
        FieldSpec(key='参数', label='接口参数', kind='multiline', default='{}', choices=(), required=False, minimum=-1000000, maximum=1000000),
        FieldSpec(key='变量', label='结果变量（可选）', kind='text', default='', choices=(), required=False, minimum=-1000000, maximum=1000000),
    )

class InstructionExecutor(BackgroundExecutor):
    TYPE_ID = '后台文字识别'
