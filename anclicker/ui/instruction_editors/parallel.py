from anclicker.ui.instruction_editors.editor import SchemaInstructionEditor
from anclicker.ui.instruction_editors.vision_tools import VisionUi
from anclicker.platform.qt_compat.QtWidgets import QLabel, QComboBox, QWidget, QHBoxLayout, QFormLayout
class ParallelUi(VisionUi):
    def setupUi(self,dialog):
        super().setupUi(dialog)
        self.errorPolicyComboBox.clear()
        self.errorPolicyComboBox.addItems(['提示异常并暂停','自动跳过','提示异常并停止'])

class ParallelEditor(SchemaInstructionEditor):
    UI_CLASS = ParallelUi
    def __init__(self,*args,**kwargs):
        super().__init__(*args,**kwargs)
        hint=QLabel(('入口填 0 时，连线后的步骤自动归属本线程，到下一个多线程分组为止。同级线程并列运行；右键可打开或取消嵌套多线程。也可填写原有独立分支入口编号。线程末尾连接结束。同名线程运行中不会重复启动。' if self.TYPE_ID == '多线程启动' else '按启动时的线程名称关闭；选择“全部线程”可统一关闭。') + '\n主窗口暂停、恢复、结束时，全部子线程跟随。子线程异常写入日志并停止该线程（自动跳过除外）。')
        hint.setWordWrap(True)
        self.ui.rootLayout.insertWidget(1,hint)
        self.test_button.setEnabled(False)
        self.test_button.setText('请在主流程中测试')
        if self.TYPE_ID == '多线程启动':
            chooser = QComboBox()
            chooser.addItem('使用后续连线（入口编号 0）', 0)
            database = getattr(self.context,'metadata',{}).get('database')
            if database is not None:
                from anclicker.storage.graph_repository import GraphRepository
                for command in GraphRepository(database.db_path).list_commands():
                    if command.type_id not in ('多线程启动','多线程关闭'):
                        chooser.addItem('#' + str(command.id) + '  ' + command.type_id + (' · ' + command.note[:40] if command.note else ''), command.id)
            chooser.currentIndexChanged.connect(lambda index: self._controls['入口编号'].setValue(chooser.itemData(index)))
            control=self._controls['入口编号']
            self.ui.visionForm.removeWidget(control)
            container=QWidget();row=QHBoxLayout(container);row.setContentsMargins(0,0,0,0)
            control.setMaximumWidth(110);row.addWidget(control);row.addWidget(chooser,1)
            self.ui.visionForm.setWidget(1,QFormLayout.FieldRole,container)
            self.ui.rows['入口编号'][0].setText('分支入口 #')
        else:
            def update_scope():
                enabled = self._controls['关闭范围'].currentText() == '指定线程'
                for widget in self.ui.rows['线程名称']: widget.setVisible(enabled)
            self._controls['关闭范围'].currentTextChanged.connect(update_scope)
            update_scope()
        self.resize(680,440 if self.TYPE_ID == '多线程启动' else 370)

    def _validate_parameters(self, parameters):
        if (self.TYPE_ID == '多线程启动' or parameters.get('关闭范围') == '指定线程') and not str(parameters.get('线程名称','')).strip():
            raise ValueError('请填写线程名称')
