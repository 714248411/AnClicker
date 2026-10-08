from instructions.common import FieldSpec, InstructionExecutorBase, actions
from instructions.流程.jump_editor import JumpEditor
from flow_jumps import TARGET_MODES, OPERATORS, compare_variables
from .变量比较_ui import Ui_InstructionEditor

class InstructionEditor(JumpEditor):
    TYPE_ID = DISPLAY_NAME = '变量比较'
    UI_CLASS = Ui_InstructionEditor
    PREFIXES = ('是','否')
    FIELDS = (
        FieldSpec('变量','左侧变量','text','',required=True),
        FieldSpec('比较条件','比较条件','choice','等于',OPERATORS),
        FieldSpec('比较对象','右侧类型','choice','固定值',('固定值','变量')),
        FieldSpec('比较值','右侧值 / 变量名','text',''),
        FieldSpec('比较类型','比较类型','choice','自动',('自动','数字','文本')),
        *(field for prefix in ('是','否') for field in (
            FieldSpec(prefix+'跳转方式',prefix+'：跳转方式','choice','连线节点',TARGET_MODES),
            FieldSpec(prefix+'目标行',prefix+'：目标行（从 1 开始）','int',1),
            FieldSpec(prefix+'项目路径',prefix+'：目标项目文件','text',''),
        )),
    )

class InstructionExecutor(InstructionExecutorBase):
    TYPE_ID = '变量比较'
    # Comparison is handled by flow_jumps; destinations by flow_jump_runtime.
    CONSUMED_FIELDS = (
        '变量', '比较条件', '比较对象', '比较值', '比较类型',
        '是跳转方式', '是目标行', '是项目路径',
        '否跳转方式', '否目标行', '否项目路径',
    )
    def execute_once(self,context,command):
        handled,result=actions.delegated(context,self.TYPE_ID,command)
        if handled: return result
        result=compare_variables(command.parameters,context.variables)
        context.emit('变量比较结果：'+('是' if result else '否'))
        return result
