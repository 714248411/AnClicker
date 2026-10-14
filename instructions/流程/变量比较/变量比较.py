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

    def __init__(self, parent=None, draft=None, context=None):
        super().__init__(parent=parent, draft=draft, context=context)
        from qt_compat.QtWidgets import QPushButton, QLabel
        self.infer_condition_button = QPushButton('根据前后指令填入变量', self)
        self.infer_condition_button.setAutoDefault(False)
        self.condition_hint_label = QLabel(self)
        self.condition_hint_label.setWordWrap(True)
        self.ui.parameterFormLayout.insertRow(1, self.infer_condition_button)
        self.ui.parameterFormLayout.insertRow(2, self.condition_hint_label)
        self._condition_hint_callback = getattr(context, 'metadata', {}).get('condition_hint')
        self.infer_condition_button.clicked.connect(lambda: self._infer_condition(replace=True))
        self._infer_condition(replace=draft is None)

    def _infer_condition(self, replace=False):
        if self._condition_hint_callback is None:
            self.condition_hint_label.setText('可手动指定变量；连接前后指令后可自动推断。')
            return
        try:
            hint = self._condition_hint_callback()
        except Exception as error:
            self.condition_hint_label.setText('无法读取相邻指令：' + str(error))
            return
        from qt_compat.QtWidgets import QCompleter
        self._controls['变量'].setCompleter(QCompleter(hint['candidates'], self))
        variable = hint['variable']
        self.condition_hint_label.setText('建议变量：' + variable if variable else
            '请手动选择变量：' + ('、'.join(hint['candidates']) or '前后指令没有可确定的变量'))
        if replace and variable:
            self._controls['变量'].setCurrentText(variable)

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
