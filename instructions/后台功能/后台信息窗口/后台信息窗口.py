from instructions.common import FieldSpec, SchemaInstructionEditor
from instructions.common.background_instruction import BackgroundMethodEditor, BackgroundExecutor, BindingEditor
from importlib import import_module
Ui_InstructionEditor = import_module('.后台信息窗口_ui', __package__).Ui_InstructionEditor

class InstructionEditor(BackgroundMethodEditor):
    TYPE_ID = DISPLAY_NAME = '后台信息窗口'
    UI_CLASS = Ui_InstructionEditor
    FIELDS = (
        FieldSpec(key='接口', label='操作', kind='choice', default='创建矩形信息窗口 · CreateFoobarRect', choices=('创建矩形信息窗口 · CreateFoobarRect', '创建圆角信息窗口 · CreateFoobarRoundRect', '创建椭圆信息窗口 · CreateFoobarEllipse', '创建自定义信息窗口 · CreateFoobarCustom', 'FoobarFillRect', '绘制文字 · FoobarDrawText', '绘制图片 · FoobarDrawPic', 'FoobarDrawLine', '刷新信息窗口 · FoobarUpdate', 'FoobarLock', 'FoobarUnlock', 'FoobarSetFont', 'FoobarTextRect', 'FoobarPrintText', 'FoobarClearText', 'FoobarTextLineGap', 'FoobarTextPrintDir', 'FoobarSetSave', '关闭信息窗口 · FoobarClose', 'FoobarStartGif', 'FoobarStopGif', 'FoobarSetTrans'), required=False, minimum=-1000000, maximum=1000000),
        FieldSpec(key='参数', label='接口参数', kind='multiline', default='{}', choices=(), required=False, minimum=-1000000, maximum=1000000),
        FieldSpec(key='变量', label='结果变量（可选）', kind='text', default='', choices=(), required=False, minimum=-1000000, maximum=1000000),
    )

class InstructionExecutor(BackgroundExecutor):
    TYPE_ID = '后台信息窗口'
