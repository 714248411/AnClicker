from instructions.common import FieldSpec, SchemaInstructionEditor
from instructions.common.background_instruction import BackgroundMethodEditor, BackgroundExecutor, BindingEditor
from importlib import import_module
Ui_InstructionEditor = import_module('.后台键鼠操作_ui', __package__).Ui_InstructionEditor

class InstructionEditor(BackgroundMethodEditor):
    TYPE_ID = DISPLAY_NAME = '后台键鼠操作'
    UI_CLASS = Ui_InstructionEditor
    FIELDS = (
        FieldSpec(key='接口', label='操作', kind='choice', default='移动至坐标 · MoveTo', choices=('移动至坐标 · MoveTo', '相对移动 · MoveR', 'MoveToEx', '鼠标左键单击 · LeftClick', '鼠标右键单击 · RightClick', '鼠标中键单击 · MiddleClick', '鼠标左键双击 · LeftDoubleClick', '按住左键 · LeftDown', '松开左键 · LeftUp', '按住右键 · RightDown', '松开右键 · RightUp', '滚轮向上 · WheelUp', '滚轮向下 · WheelDown', '按住按键 · KeyDown', '松开按键 · KeyUp', '按一下按键 · KeyPress', 'KeyDownChar', 'KeyUpChar', 'KeyPressChar', 'KeyPressStr', '发送文本 · SendString', '发送文本（方式二） · SendString2', 'SetMouseDelay', 'SetKeypadDelay', '按住中键 · MiddleDown', '松开中键 · MiddleUp'), required=False, minimum=-1000000, maximum=1000000),
        FieldSpec(key='参数', label='接口参数', kind='multiline', default='{}', choices=(), required=False, minimum=-1000000, maximum=1000000),
        FieldSpec(key='变量', label='结果变量（可选）', kind='text', default='', choices=(), required=False, minimum=-1000000, maximum=1000000),
    )

class InstructionExecutor(BackgroundExecutor):
    TYPE_ID = '后台键鼠操作'
