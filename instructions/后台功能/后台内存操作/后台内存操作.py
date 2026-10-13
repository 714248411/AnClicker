from instructions.common import FieldSpec, SchemaInstructionEditor
from instructions.common.background_instruction import BackgroundMethodEditor, BackgroundExecutor, BindingEditor
from importlib import import_module
Ui_InstructionEditor = import_module('.后台内存操作_ui', __package__).Ui_InstructionEditor

class InstructionEditor(BackgroundMethodEditor):
    TYPE_ID = DISPLAY_NAME = '后台内存操作'
    UI_CLASS = Ui_InstructionEditor
    FIELDS = (
        FieldSpec(key='接口', label='操作', kind='choice', default='读取整数 · ReadInt', choices=('读取整数 · ReadInt', '读取单精度数值 · ReadFloat', '读取双精度数值 · ReadDouble', '读取字符串 · ReadString', '读取字节数据 · ReadData', '写入整数 · WriteInt', '写入单精度数值 · WriteFloat', '写入双精度数值 · WriteDouble', '写入字符串 · WriteString', '写入字节数据 · WriteData', '搜索整数 · FindInt', '搜索单精度数值 · FindFloat', '搜索双精度数值 · FindDouble', '搜索字符串 · FindString', '搜索字节数据 · FindData', 'FindIntEx', 'FindFloatEx', 'FindDoubleEx', 'FindStringEx', 'FindDataEx', '获取模块基址 · GetModuleBaseAddr', 'IntToData', 'FloatToData', 'DoubleToData', 'StringToData'), required=False, minimum=-1000000, maximum=1000000),
        FieldSpec(key='参数', label='接口参数', kind='multiline', default='{}', choices=(), required=False, minimum=-1000000, maximum=1000000),
        FieldSpec(key='变量', label='结果变量（可选）', kind='text', default='', choices=(), required=False, minimum=-1000000, maximum=1000000),
    )

class InstructionExecutor(BackgroundExecutor):
    TYPE_ID = '后台内存操作'
