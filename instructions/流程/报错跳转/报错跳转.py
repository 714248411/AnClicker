from instructions.common import FieldSpec, InstructionExecutorBase, actions
from instructions.流程.jump_editor import JumpEditor
from flow_jumps import TARGET_MODES
from .报错跳转_ui import Ui_InstructionEditor

class InstructionEditor(JumpEditor):
    TYPE_ID = DISPLAY_NAME = '报错跳转'
    UI_CLASS = Ui_InstructionEditor
    FIELDS = (
        FieldSpec('跳转方式','跳转方式','choice','连线节点',TARGET_MODES),
        FieldSpec('目标行','目标行（表格序号，从 1 开始）','int',1),
        FieldSpec('项目路径','目标项目文件','text',''),
    )

class InstructionExecutor(InstructionExecutorBase):
    TYPE_ID = '报错跳转'
    CONSUMED_FIELDS = ('跳转方式','目标行','项目路径')
    def execute_once(self,context,command):
        handled,result=actions.delegated(context,self.TYPE_ID,command)
        if handled: return result
        raise ValueError('报错跳转不是普通指令；请从源指令右侧异常接口连接此模块。')
