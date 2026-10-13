from instructions.common import FieldSpec, SchemaInstructionEditor
from instructions.common.background_instruction import BackgroundMethodEditor, BackgroundExecutor, BindingEditor
from importlib import import_module
Ui_InstructionEditor = import_module('.后台答题器_ui', __package__).Ui_InstructionEditor

class InstructionEditor(BackgroundMethodEditor):
    TYPE_ID = DISPLAY_NAME = '后台答题器'
    UI_CLASS = Ui_InstructionEditor
    FIELDS = (
        FieldSpec(key='接口', label='操作', kind='choice', default='截取答题区域 · FaqCapture', choices=('截取答题区域 · FaqCapture', '载入答题图片 · FaqCaptureFromFile', '释放答题图像 · FaqRelease', '发送答题图片 · FaqSend', '异步发送答题图片 · FaqPost', '获取答题结果 · FaqFetch', '获取答题图像大小 · FaqGetSize', '取消答题任务 · FaqCancel', '截取答题图像字符串 · FaqCaptureString', '查询答题提交状态 · FaqIsPosted'), required=False, minimum=-1000000, maximum=1000000),
        FieldSpec(key='参数', label='接口参数', kind='multiline', default='{}', choices=(), required=False, minimum=-1000000, maximum=1000000),
        FieldSpec(key='变量', label='结果变量（可选）', kind='text', default='', choices=(), required=False, minimum=-1000000, maximum=1000000),
    )

class InstructionExecutor(BackgroundExecutor):
    TYPE_ID = '后台答题器'
