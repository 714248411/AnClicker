"""Window-relative keyboard and mouse instruction editor."""
from anclicker.platform.qt_compat.QtCore import Signal
from anclicker.ui.instruction_editors.window_settings_footer import add_window_footer
from anclicker.platform.qt_compat.QtCore import Qt
from anclicker.platform.qt_compat.QtWidgets import (QDialog, QVBoxLayout, QFormLayout, QComboBox,
    QSpinBox, QLineEdit, QLabel, QPushButton, QDialogButtonBox, QMessageBox, QApplication, QHBoxLayout)
from anclicker.domain.instruction_interfaces import InstructionEditorInterface
from anclicker.domain.instructions import InstructionDraft
from anclicker.ui.background_window_picker import BackgroundWindowPicker, pick_background_window
from anclicker.instructions.窗口键鼠.窗口键鼠.schema import FIELDS, OPERATIONS


class PointPicker(BackgroundWindowPicker):
    def __init__(self, target):
        super().__init__()
        self.target = self.windows.resolve(target)
        self.message = '点击所选窗口内容区取点 · Esc / 右键取消'

    def mouseReleaseEvent(self, event):
        if event.button() == Qt.RightButton:
            self.reject()
        elif event.button() == Qt.LeftButton:
            try:
                self.windows.validate(self.target)
                hwnd = int(self.target['窗口句柄'])
                x, y = self.windows.gui.ScreenToClient(hwnd, self.windows.cursor_position())
                width, height = self.windows.size(self.target)
                if not (0 <= x < width and 0 <= y < height):
                    raise ValueError('请点击所选窗口的内容区')
                self.selection = (x, y)
                self.accept()
            except Exception as error:
                self.message = str(error) + ' · Esc 取消'
                self.update()


class InstructionEditor(QDialog, InstructionEditorInterface):
    test_requested = Signal(object)
    TYPE_ID = DISPLAY_NAME = '窗口键鼠'
    FIELDS = FIELDS
    OPERATIONS = OPERATIONS
    DEFAULT_OPERATION = '左键单击'

    def __init__(self, parent=None, draft=None, context=None):
        super().__init__(parent)
        self.context = context
        self.target = {}
        self.setWindowTitle(self.DISPLAY_NAME)
        self.resize(480, 420)
        layout = QVBoxLayout(self)
        self.target_label = QLabel('未选择窗口')
        self.target_label.setWordWrap(True)
        self.select = QPushButton('点选目标窗口')
        self.select.clicked.connect(self.select_window)
        target_row = QHBoxLayout()
        target_row.addWidget(self.select)
        target_row.addWidget(self.target_label, 1)
        layout.addLayout(target_row)
        form = QFormLayout()
        layout.addLayout(form)
        self.mode = QComboBox()
        self.mode.addItems(['前台', '后台'])
        form.addRow('执行模式:', self.mode)
        from anclicker.platform.background_binding import PRESETS, CUSTOM
        self.background_preset = QComboBox()
        self.background_preset.addItems([name for name in PRESETS if name != CUSTOM])
        form.addRow('大漠后台方案:', self.background_preset)
        self.background_preset_label = form.labelForField(self.background_preset)
        self.background_preset.setToolTip('与大漠绑定指令共用后台1–4；成功后新建指令自动沿用。')
        self.mode.currentTextChanged.connect(self._update_background_mode)
        hint = QLabel(('坐标以窗口内容区左上角为原点。' if any(op not in ('组合键', '输入内容') for op in self.OPERATIONS) else '选择常用按键，或填写组合键，例如 ctrl+shift+s。') + '后台自动绑定；前台置顶激活后执行，再恢复窗口状态。')
        hint.setWordWrap(True)
        layout.addWidget(hint)
        self.operation = QComboBox()
        self.operation.addItems(self.OPERATIONS)
        form.addRow('操作:', self.operation)
        self.pick_start = QPushButton('点选位置（相对坐标）')
        self.pick_end = QPushButton('点选拖拽结束位置')
        pick_row = QHBoxLayout()
        pick_row.addWidget(self.pick_start)
        pick_row.addWidget(self.pick_end)
        form.addRow(pick_row)
        self.fields = {}
        self.rows = {}
        for key, label in [('X', '相对 X:'), ('Y', '相对 Y:'), ('结束X', '结束 X:'), ('结束Y', '结束 Y:'), ('滚轮', '滚轮格数:')]:
            widget = QSpinBox()
            widget.setRange(-100000 if key == '滚轮' else 0, 100000)
            form.addRow(label, widget)
            self.fields[key] = widget
            self.rows[key] = (form.labelForField(widget), widget)
        self.keys = QComboBox()
        self.keys.setEditable(True)
        self.keys.addItems(['ctrl+c', 'ctrl+v', 'ctrl+a', 'ctrl+s', 'enter', 'tab', 'escape', 'alt+f4'])
        form.addRow('按键:', self.keys)
        self.rows['按键'] = (form.labelForField(self.keys), self.keys)
        self.pick_start.clicked.connect(lambda: self.pick_point(False))
        self.pick_end.clicked.connect(lambda: self.pick_point(True))
        common = QFormLayout()
        self.repeat = QSpinBox()
        self.repeat.setRange(1, 1000000)
        self.policy = QComboBox()
        self.policy.addItems(['提示异常并暂停', '提示异常并停止', '自动跳过'])
        self.note = QLineEdit()
        common.addRow('重复次数:', self.repeat)
        common.addRow('异常处理:', self.policy)
        common.addRow('备注:', self.note)
        layout.addLayout(common)
        buttons = QDialogButtonBox(QDialogButtonBox.Ok | QDialogButtonBox.Cancel)
        buttons.button(QDialogButtonBox.Ok).setText('确定')
        buttons.button(QDialogButtonBox.Cancel).setText('取消')
        buttons.accepted.connect(self.accept)
        buttons.rejected.connect(self.reject)
        add_window_footer(self, layout, buttons)
        for button in (self.select, self.pick_start, self.pick_end):
            button.setAutoDefault(False)
        self.operation.currentTextChanged.connect(self.update_fields)
        self.load_draft(draft or InstructionDraft(self.TYPE_ID))

    def _update_background_mode(self, *_):
        background = self.mode.currentText() == '后台'
        self.background_preset.setVisible(background)
        self.background_preset_label.setVisible(background)
        if background:
            from anclicker.platform.background_preload import start_preload
            start_preload()

    def update_fields(self, *_):
        op = self.operation.currentText()
        for key, widgets in self.rows.items():
            visible = (op == '组合键' if key == '按键' else
                       op == '鼠标拖拽' if key in ('结束X', '结束Y') else
                       op == '滚轮滑动' if key == '滚轮' else op != '组合键')
            for widget in widgets:
                widget.setVisible(visible)
        self.pick_start.setVisible(op != '组合键')
        self.pick_end.setVisible(op == '鼠标拖拽')
        self.pick_start.setEnabled(bool(self.target))
        self.pick_end.setEnabled(bool(self.target))

    def select_window(self):
        try:
            target = pick_background_window(self)
            if target:
                self.target = target
                self.show_target()
                self.update_fields()
        except Exception as error:
            QMessageBox.warning(self, '选择窗口', str(error))

    def show_target(self):
        self.target_label.setText(self.target.get('窗口标题') or self.target.get('窗口类名') or '未选择窗口')

    def pick_point(self, end):
        picker = None
        visible = []
        try:
            if not self.target:
                raise ValueError('请先点选目标窗口')
            picker = PointPicker(self.target)
            visible = [(w, w.windowOpacity()) for w in QApplication.topLevelWidgets()
                       if w is not picker and w.isVisible()]
            for widget, _ in visible:
                widget.setWindowOpacity(0)
            if picker.exec() == QDialog.Accepted:
                x, y = picker.selection
                self.fields['结束X' if end else 'X'].setValue(x)
                self.fields['结束Y' if end else 'Y'].setValue(y)
                self.point_selected(x, y, end)
        except Exception as error:
            QMessageBox.warning(self, '点选位置', str(error))
        finally:
            if picker is not None:
                picker.close()
                picker.deleteLater()
            for widget, opacity in visible:
                try:
                    widget.setWindowOpacity(opacity)
                except RuntimeError:
                    pass
            self.raise_()
            self.activateWindow()

    def point_selected(self, x, y, end):
        pass

    def load_draft(self, draft):
        draft = draft if isinstance(draft, InstructionDraft) else InstructionDraft.from_mapping(draft)
        p = draft.parameters
        self.target = dict(p.get('窗口') or {})
        self.show_target()
        from anclicker.platform.background_binding import selected_preset, display_preset, CUSTOM
        from anclicker.platform.background_preferences import preferred_preset
        self._background_parameters = {key:p[key] for key in ('绑定方案','图像模式','鼠标模式','键盘模式','绑定模式','绑定等待') if key in p}
        preset = selected_preset(p) if any(key in p for key in ('模式','窗口','绑定方案','图像模式','鼠标模式','键盘模式')) else preferred_preset()
        if preset == CUSTOM and self.background_preset.findText(CUSTOM) < 0:
            self.background_preset.addItem(CUSTOM)
        self.background_preset.setCurrentText(display_preset(preset))
        self.mode.setCurrentText(p.get('模式', '前台'))
        self._update_background_mode()
        self.operation.setCurrentText(p.get('操作', self.DEFAULT_OPERATION))
        for key, widget in self.fields.items():
            widget.setValue(int(p.get(key, 1 if key == '滚轮' else 0)))
        self.keys.setCurrentText(p.get('按键', 'ctrl+c'))
        self.repeat.setValue(draft.repeat_count)
        if self.policy.findText(draft.error_policy) < 0:
            self.policy.addItem(draft.error_policy)
        self.policy.setCurrentText(draft.error_policy)
        self.note.setText(draft.note)
        self.update_fields()

    def get_draft(self):
        op = self.operation.currentText()
        p = {'窗口': dict(self.target), '模式': self.mode.currentText(), '操作': op}
        p.update(self._background_parameters)
        p['绑定方案'] = self.background_preset.currentText()
        if op == '组合键':
            p['按键'] = self.keys.currentText()
        else:
            for key, widget in self.fields.items():
                if key in ('X', 'Y') or (op == '鼠标拖拽' and key in ('结束X', '结束Y')) or (op == '滚轮滑动' and key == '滚轮'):
                    p[key] = widget.value()
        return InstructionDraft(self.TYPE_ID, p, repeat_count=self.repeat.value(),
                                error_policy=self.policy.currentText(), note=self.note.text())

    def accept(self):
        if not self.target:
            QMessageBox.warning(self, '窗口键鼠', '请先选择目标窗口')
            return
        super().accept()
