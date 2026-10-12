"""按下键盘：独立参数编辑器与执行器。"""

from __future__ import annotations

from instructions.common import FieldSpec, InstructionExecutorBase, SchemaInstructionEditor
from instructions.common import actions
from instructions.models import CommandRecord, ExecutionContext
from .按下键盘_ui import Ui_InstructionEditor


class InstructionEditor(SchemaInstructionEditor):
    TYPE_ID = "按下键盘"
    DISPLAY_NAME = "按下键盘"
    UI_CLASS = Ui_InstructionEditor
    FIELDS = (
        FieldSpec("按键", "按键（用 + 组合）", "text", "enter", required=True),
        FieldSpec("按压时长", "按压时长（毫秒）", "int", 50, minimum=0, maximum=3600000),
    )

    def __init__(self, parent=None, draft=None, context=None):
        super().__init__(parent, draft, context)
        from qt_compat.QtWidgets import QComboBox, QHBoxLayout, QPushButton, QWidget
        form = self.ui.parameterFormLayout
        keys = self._controls['按键']
        duration = self._controls['按压时长']
        for row, control in ((0, keys), (1, duration)):
            form.removeWidget(control)
            holder = QWidget(self)
            layout = QHBoxLayout(holder)
            layout.setContentsMargins(0, 0, 0, 0)
            layout.addWidget(control, 1)
            if row == 0:
                self.capture_button = QPushButton('捕获按键', holder)
                self.capture_button.setAutoDefault(False)
                self.capture_button.clicked.connect(self.capture_keys)
                layout.addWidget(self.capture_button)
            else:
                self.duration_presets = QComboBox(holder)
                self.duration_presets.addItem('常用时长（毫秒）', None)
                for value in (5, 10, 20, 30, 50, 100, 200, 500, 1000, 2000, 5000):
                    self.duration_presets.addItem(str(value), value)
                self.duration_presets.activated.connect(self.apply_duration_preset)
                layout.addWidget(self.duration_presets)
            form.setWidget(row, form.ItemRole.FieldRole, holder)

    def apply_duration_preset(self, index):
        value = self.duration_presets.itemData(index)
        if value is not None:
            self._controls['按压时长'].setValue(value)

    def capture_keys(self):
        from qt_compat.QtWidgets import QDialog, QMessageBox
        from instructions.common.input_controls import KeyCaptureDialog
        owner = self.parentWidget()
        while owner is not None and not hasattr(owner, 'unregister_global_shortcut_keys'):
            owner = owner.parentWidget()
        if owner is not None and owner.command_thread.isRunning():
            QMessageBox.information(self, '请先停止任务', '运行时不能捕获按键，请先停止任务。')
            return
        dialog = KeyCaptureDialog(self)
        try:
            if owner is not None:
                owner.unregister_global_shortcut_keys()
            if dialog.exec() == QDialog.DialogCode.Accepted and dialog.value:
                self._controls['按键'].setText(dialog.value)
        finally:
            dialog.deleteLater()
            if owner is not None:
                owner.register_global_shortcut_keys()


class InstructionExecutor(InstructionExecutorBase):
    TYPE_ID = "按下键盘"

    def execute_once(self, context: ExecutionContext, command: CommandRecord):
        if command.type_id != self.TYPE_ID:
            raise ValueError(f"按下键盘执行器不能执行{command.type_id}")
        delegated_, result_ = actions.delegated(context, self.TYPE_ID, command)
        if delegated_:
            return result_
        keys_ = [item_.strip() for item_ in str(actions.parameter(command.parameters, "按键", default="enter")).split("+") if item_.strip()]
        duration_ = float(actions.parameter(command.parameters, "按压时长", default=50)) / 1000
        gui_ = actions.pyautogui_module()
        recorded_action_ = command.parameters.get("录制动作")
        if recorded_action_ in {"按下", "松开"}:
            from recorded_input import key_event
            key_ = str(command.parameters["按键"])
            held_ = context.metadata.setdefault("recorded_keys", set())
            if recorded_action_ == "按下":
                held_.add(key_)
                gui_.failSafeCheck()
                key_event(context, key_, True, gui_)
            else:
                key_event(context, key_, False, gui_)
                held_.discard(key_)
            return key_
        pressed_ = []
        try:
            for key_ in keys_:
                if not actions.wait_interruptibly(context, 0):
                    return None
                # keyDown can send input and then raise during its fail-safe/pause.
                pressed_.append(key_)
                gui_.keyDown(key_)
            if not actions.wait_interruptibly(context, duration_):
                return None
        finally:
            actions.release_inputs(context, gui_, keys=pressed_)
        context.emit(f"按下键盘：{'+'.join(keys_)}")
        return keys_
