from recording_layout import panel, control_row, inline_group, setup_page
"""Visible, opt-in recording workspace; never installs hooks during startup."""
import json
import time
import sys

from qt_compat.QtCore import Signal, QTimer, Qt
from qt_compat.QtGui import QShortcut, QKeySequence
from qt_compat.QtWidgets import (QWidget, QVBoxLayout, QHBoxLayout, QLabel, QPushButton,
                               QCheckBox, QSpinBox, QDoubleSpinBox, QTableWidget, QTableWidgetItem,
                               QHeaderView, QAbstractItemView, QMessageBox, QFrame, QSizePolicy)
from input_recording import RecordingBuffer, GlobalInputRecorder, events_to_drafts, recording_at_speed


class RecordingView(QWidget):
    stopRequested = Signal()
    captureFailed = Signal(str)

    def __init__(self, window, parent=None):
        super().__init__(parent)
        self.window = window
        self.setObjectName("recordingView")
        self.buffer = RecordingBuffer()
        self.recorder = None
        self.countdown = 0
        self.drafts = []
        self.written = False
        self.was_hidden = False
        self.own_rect = None
        self.own_focus = False
        self.native_window = None
        if sys.platform == "win32":
            import ctypes
            from ctypes import wintypes
            self.native_window = (ctypes.WinDLL("user32", use_last_error=True),
                                  int(window.winId()), wintypes.RECT)
            user32 = self.native_window[0]
            user32.GetForegroundWindow.restype = ctypes.c_void_p
            user32.GetAncestor.argtypes = [ctypes.c_void_p, ctypes.c_uint]
            user32.GetAncestor.restype = ctypes.c_void_p
            user32.GetWindowRect.argtypes = [ctypes.c_void_p, ctypes.POINTER(wintypes.RECT)]
        layout = QVBoxLayout(self)
        setup_page(layout)
        description = "操作顺序\n设置录制选项 → 开始录制 → 切换到目标窗口操作 → 停止录制 → 检查预览 → 写入表格与流程图。\n\n开始与停止\n开始倒计时可设为 1～10 秒，默认 3 秒，倒计时结束后才开始记录。录制支持鼠标点击、双击、拖拽、侧键、双向滚轮，以及键盘按下和松开（含组合键）。\n按 Esc 或点击停止按钮结束；默认也可按 F8。需要录入 F8 时，先取消“F8 停止录制”，此时主窗口不会自动隐藏。倒计时期间可用 Esc 或停止按钮取消。\n\n录制选项\n“录制轨迹”默认不勾选：不记录普通鼠标移动，但保留按住鼠标拖拽的过程；勾选后记录普通移动，事件数量会增加。\n“录制时隐藏主窗口”默认开启，停止后恢复主窗口；主窗口内的操作会被排除。\n“保留操作时间间隔”默认开启，回放保留操作节奏；取消后不保留原来的等待节奏。\n“自动连接录制流程”用于连接本次写入的录制步骤。\n“停止后自动写入（原速）”默认关闭；需要删除或接续录制时，请保持关闭，先检查预览。\n\n预览、删除与接续\n停止后可选择一行或多行，右键删除并确认；预览中的参数不能直接编辑，写入后可在表格或流程图中调整。\n接续录制：先选中一条尚未写入的步骤，再点击“接续录制”，新操作会插在该步骤下方，原有后续步骤保留。开始前请手动将目标窗口恢复到需要接续的状态，程序不会自动执行前面的步骤。\n\n写入与倍速\n“写入表格与流程图”按原速追加；也可选择 0.10～10.00 倍速写入。大于 1 加快，小于 1 放慢，例如 1.25 倍可将 10 秒的录制节奏缩短为 8 秒；倍速需要保留操作时间间隔。\n同一份预览只能写入一次。写入后请到表格或流程图修改、删除；清空预览不会删除已写入的指令。重新开始录制会询问是否丢弃未写入内容。\n\n使用提醒\n回放前保持目标窗口位置、屏幕缩放及界面状态一致，先检查坐标和等待时间。键鼠录制可能记录敏感输入，请勿录入密码等信息。\n最多记录 20000 个事件，达到上限自动停止。硬件 Fn 等按键受系统限制；原始键码宜在同一系统回放。macOS 需要辅助功能和输入监控权限，Linux 需要 X11。"
        from recording_help import recording_header
        layout.addLayout(recording_header(self, '键盘鼠标录制', description))
        self.settings_panel, settings = panel(self, "录制设置")
        layout.addWidget(self.settings_panel)
        options = control_row()
        countdown_label = QLabel("倒计时（秒）")
        countdown_label.setSizePolicy(QSizePolicy.Policy.Maximum, QSizePolicy.Policy.Preferred)
        self.delay = QSpinBox()
        self.delay.setRange(1, 10)
        self.delay.setValue(3)
        self.delay.setSizePolicy(QSizePolicy.Policy.Maximum, QSizePolicy.Policy.Fixed)
        self.delay.setMinimumWidth(64)
        self.delay.setAlignment(Qt.AlignmentFlag.AlignCenter)
        self.countdown_group = inline_group(countdown_label, self.delay)
        options.addWidget(self.countdown_group)
        self.f8_option = QCheckBox("F8 停止录制")
        self.f8_option.setChecked(True)
        self.f8_option.setSizePolicy(QSizePolicy.Policy.Maximum, QSizePolicy.Policy.Fixed)
        options.addWidget(self.f8_option)
        separator = QFrame(self)
        separator.setObjectName('recordingOptionSeparator')
        separator.setFrameShape(QFrame.Shape.VLine)
        separator.setFixedSize(1, 16)
        options.addWidget(separator, 0, Qt.AlignmentFlag.AlignVCenter)
        self.trajectory_option = QCheckBox('录制轨迹')
        self.trajectory_option.setChecked(False)
        self.trajectory_option.setToolTip('勾选后记录普通鼠标移动；不勾选仍记录点击、滚轮，以及按住鼠标拖拽的移动过程。')
        self.trajectory_option.setSizePolicy(QSizePolicy.Policy.Maximum, QSizePolicy.Policy.Fixed)
        options.addWidget(self.trajectory_option)
        options.addStretch(1)
        self.hide_option = QCheckBox("录制时隐藏主窗口")
        self.hide_option.setChecked(True)
        self.timing_option = QCheckBox("保留操作时间间隔")
        self.timing_option.setChecked(True)
        self.connect_option = QCheckBox("自动连接录制流程")
        self.connect_option.setChecked(True)
        self.auto_option = QCheckBox("停止后自动写入（原速）")
        self.auto_option.setChecked(False)
        self.auto_option.setToolTip("默认停止后预览，再选择原速或倍速写入；勾选后自动按原速写入。")
        settings.addLayout(options)
        options = control_row()
        for option in (self.hide_option, self.timing_option, self.connect_option, self.auto_option):
            options.addWidget(option)
        options.addStretch()
        settings.addLayout(options)
        self.actions_panel, actions = panel(self, "录制操作")
        layout.addWidget(self.actions_panel)
        controls = control_row()
        self.start_button = QPushButton("开始录制")
        self.start_button.setObjectName("accentButton")
        self.stop_button = QPushButton("停止录制（Esc / F8）")
        self.stop_button.setObjectName("dangerButton")
        self.continue_button = QPushButton("接续录制")
        self.continue_button.setToolTip("选中步骤后，在该步骤下方插入新录制内容")
        from recording_continuation import begin_continuation
        self.continue_button.clicked.connect(lambda: begin_continuation(self))
        self.write_button = QPushButton("写入表格与流程图")
        self.speed = QDoubleSpinBox()
        self.speed.setRange(0.1, 10.0)
        self.speed.setDecimals(2)
        self.speed.setSingleStep(0.25)
        self.speed.setValue(1.25)
        self.speed.setSuffix(" ×")
        self.speed.setMinimumWidth(80)
        self.speed.setToolTip("自定义 0.10–10.00 倍速；1.25 倍将 10 秒录制缩短至 8 秒。需保留操作时间间隔。")
        self.speed_write_button = QPushButton("按倍速写入")
        self.speed_write_button.setToolTip("按所选倍速写入表格与流程图")
        self.speed.valueChanged.connect(lambda value: self.speed_write_button.setToolTip(
            f"按 {value:g} 倍速写入表格与流程图"))
        self.speed_write_button.clicked.connect(self.write_at_speed)
        self.clear_button = QPushButton("清空录制预览")
        self.start_button.clicked.connect(self.begin)
        self.stop_button.clicked.connect(self.finish)
        self.escape_shortcut = QShortcut(QKeySequence("Esc"), self)
        self.escape_shortcut.activated.connect(self.finish)
        self.write_button.clicked.connect(lambda: self.write())
        self.clear_button.clicked.connect(self.clear)
        for button in (self.start_button, self.stop_button, self.continue_button, self.clear_button):
            controls.addWidget(button)
        controls.addStretch()
        actions.addLayout(controls)
        write_controls = controls
        write_controls.addWidget(self.write_button)
        self.speed.setAlignment(Qt.AlignmentFlag.AlignCenter)
        write_controls.addWidget(inline_group(self.speed, self.speed_write_button))
        write_controls.addStretch()
        self.f8_option.toggled.connect(self.update_stop_mode)
        self.status = QLabel("未录制 · 不录普通轨迹，拖拽正常保留 · 最多 20000 个事件")
        self.status.setToolTip("勾选录制轨迹后，普通鼠标移动每 10 毫秒采样；最多记录 20000 个事件。")
        self.status.setWordWrap(True)
        self.status.setObjectName("taskStats")
        layout.addWidget(self.status)
        self.preview = QTableWidget(0, 3)
        self.preview.setHorizontalHeaderLabels(["序号", "指令", "参数"])
        self.preview.setEditTriggers(QAbstractItemView.EditTrigger.NoEditTriggers)
        from recording_preview_menu import RecordingPreviewMenu
        self.preview_menu = RecordingPreviewMenu(self)
        self.preview.horizontalHeader().setSectionResizeMode(2, QHeaderView.ResizeMode.Stretch)
        layout.addWidget(self.preview, 1)
        self.timer = QTimer(self)
        self.timer.setInterval(100)
        self.timer.timeout.connect(self.tick)
        self.stopRequested.connect(self.finish)
        self.captureFailed.connect(self.failed)
        self.update_buttons()

    @property
    def busy(self):
        return bool(self.countdown or self.recorder is not None)

    def update_buttons(self):
        self.start_button.setEnabled(not self.busy)
        self.stop_button.setEnabled(self.busy)
        self.continue_button.setEnabled(not self.busy and bool(self.drafts) and not self.written)
        self.write_button.setEnabled(not self.busy and bool(self.drafts) and not self.written)
        self.speed_write_button.setEnabled(self.write_button.isEnabled())
        self.speed.setEnabled(not self.busy and not self.written)
        self.clear_button.setEnabled(not self.busy and bool(self.drafts))
        for control in (self.delay, self.f8_option, self.trajectory_option, self.hide_option, self.timing_option, self.connect_option, self.auto_option):
            control.setEnabled(not self.busy)
        self.hide_option.setEnabled(not self.busy and self.f8_option.isChecked())

    def update_stop_mode(self, enabled):
        if not enabled:
            self.hide_option.setChecked(False)
        self.stop_button.setText("停止录制（Esc / F8）" if enabled else "停止录制（Esc）")
        self.update_buttons()

    def begin(self, *, continuation=False):
        if getattr(self.window, '_update_preparing', False):
            self.status.setText('正在准备更新，暂时无法开始录制。')
            return
        if self.busy:
            return
        if (self.window.command_thread.isRunning() or bool(getattr(self.window, 'task_scheduler', None) and self.window.task_scheduler.busy)) or getattr(getattr(getattr(self.window, "view_workspace", None), "web_recording_page", None), "busy", False):
            QMessageBox.warning(self, "无法录制", "请先停止正在运行的任务。")
            return
        if not continuation and self.drafts and not self.written and QMessageBox.question(
                self, "重新录制", "上次录制尚未写入，确定丢弃并重新录制吗？"
                ) != QMessageBox.StandardButton.Yes:
            return
        self.drafts, self.written = [], False
        self.preview.setRowCount(0)
        self.countdown = self.delay.value()
        self.deadline = time.monotonic() + self.countdown
        self.timer.start()
        self.update_buttons()
        self.tick()

    def tick(self):
        if self.countdown:
            remaining = self.deadline - time.monotonic()
            if remaining > 0:
                self.status.setText(f"{max(1, int(remaining + 0.999))} 秒后开始 · Esc 或停止按钮取消")
                return
            self.countdown = 0
            try:
                self.refresh_exclusion()
                if self.hide_option.isChecked():
                    self.was_hidden = True
                    self.window.hide()
                    self.own_rect, self.own_focus = None, False
                self.buffer.start()
                self.recorder = GlobalInputRecorder(
                    self.buffer, self.stopRequested.emit, self.captureFailed.emit,
                    self.exclude_mouse, self.exclude_keyboard,
                    stop_with_f8=self.f8_option.isChecked(),
                    record_trajectory=self.trajectory_option.isChecked())
                self.recorder.start()
                self.capture_started = time.monotonic()
                self.update_buttons()
            except Exception as error:
                self.failed(str(error))
                return
        if self.recorder is not None:
            self.refresh_exclusion()
            if self.buffer.full:
                self.finish()
                self.status.setText(self.status.text() + f" · 达到 {self.buffer.limit} 事件上限，已自动停止")
            elif time.monotonic() - self.capture_started > 1 and any(
                    not listener.is_alive() for listener in self.recorder.listeners):
                self.failed("输入监听器已退出，请检查输入监听权限或桌面环境。")
            else:
                stop_tip = "Esc / F8 或停止按钮结束" if self.f8_option.isChecked() else "Esc 或停止按钮结束"
                trajectory_tip = "包含鼠标轨迹" if self.trajectory_option.isChecked() else "不录普通轨迹 · 保留拖拽"
                self.status.setText(f"录制中 · {len(self.buffer.snapshot())} 个事件 · {trajectory_tip} · {stop_tip}")

    def refresh_exclusion(self):
        rect = self.window.frameGeometry()
        self.own_rect = (rect.left(), rect.top(), rect.right(), rect.bottom()) if self.window.isVisible() else None
        self.own_focus = self.window.isVisible() and self.window.isActiveWindow()

    def exclude_mouse(self, x, y):
        rect = self.own_rect
        if rect and self.native_window is not None:
            import ctypes
            user32, handle, rect_type = self.native_window
            native_rect = rect_type()
            if user32.GetWindowRect(handle, ctypes.byref(native_rect)):
                rect = (native_rect.left, native_rect.top, native_rect.right, native_rect.bottom)
        return bool(rect and rect[0] <= x <= rect[2] and rect[1] <= y <= rect[3])

    def exclude_keyboard(self):
        if self.native_window is not None:
            user32, handle, _ = self.native_window
            foreground = user32.GetForegroundWindow()
            return user32.GetAncestor(foreground, 3) == handle
        return self.own_focus

    def finish(self, *, auto_write=True):
        if not self.busy:
            return
        self.countdown = 0
        self.timer.stop()
        recorder, self.recorder = self.recorder, None
        if recorder is not None:
            recorder.stop()
            from recording_continuation import finish_continuation
            finish_continuation(self, events_to_drafts(self.buffer.snapshot(), self.timing_option.isChecked()))
        elif getattr(self, "_continuation", None) is not None:
            from recording_continuation import finish_continuation
            finish_continuation(self, [])
        if self.was_hidden:
            self.was_hidden = False
            self.window.show()
            self.window.raise_()
            self.window.activateWindow()
        self.render_preview()
        self.status.setText(f"录制结束 · {len(self.drafts)} 条指令（尚未写入）" if self.drafts else "录制已停止，无操作记录")
        self.update_buttons()
        if auto_write and self.auto_option.isChecked() and self.drafts:
            self.write()

    def render_preview(self):
        self.preview.setRowCount(len(self.drafts))
        for row, draft in enumerate(self.drafts):
            for column, text in enumerate((str(row + 1), draft.type_id,
                                           json.dumps(draft.parameters, ensure_ascii=False))):
                self.preview.setItem(row, column, QTableWidgetItem(text))

    def write_at_speed(self):
        self.speed.interpretText()
        self.write(speed=self.speed.value())

    def write(self, *, speed=1.0):
        if self.busy or not self.drafts or self.written:
            return
        if (self.window.command_thread.isRunning() or bool(getattr(self.window, 'task_scheduler', None) and self.window.task_scheduler.busy)):
            QMessageBox.warning(self, "无法写入", "请先停止正在运行的任务。")
            return
        try:
            workspace = self.window.workspace
            drafts = recording_at_speed(self.drafts, speed)
            ids = workspace.repository.append_recording(drafts, connect=self.connect_option.isChecked())
            self.written = True  # Never insert a duplicate if projection refresh fails.
            self.update_buttons()
            workspace.reload_graph()
            workspace.graphFinalized.emit(False)
            self.status.setText(f"已按 {speed:g} 倍速追加 {len(ids)} 条指令 · 表格、流程图与多功能已同步 · 未修改原有指令")
            workspace.statusMessage.emit(f"键鼠录制已写入：{len(ids)} 条指令")
        except Exception as error:
            QMessageBox.warning(self, "录制写入失败", str(error))

    def failed(self, error):
        self.finish(auto_write=False)
        self.status.setText(f"录制已停止：{error}")
        QMessageBox.warning(self, "录制不可用", f"{error}\n\n请检查 macOS 辅助功能/输入监控权限，或 Linux X11 桌面环境。已有预览仍可手动写入。")

    def clear(self):
        if self.busy:
            return
        if self.drafts and not self.written and QMessageBox.question(
                self, "清空预览", "确定丢弃未写入的录制内容吗？") != QMessageBox.StandardButton.Yes:
            return
        self.drafts, self.written = [], False
        self.preview.setRowCount(0)
        self.status.setText("录制预览已清空，不影响表格和流程图中的指令")
        self.update_buttons()

    def shutdown(self):
        self.finish(auto_write=False)
