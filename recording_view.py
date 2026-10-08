"""Visible, opt-in recording workspace; never installs hooks during startup."""
import json
import time
import sys

from qt_compat.QtCore import Signal, QTimer
from qt_compat.QtGui import QShortcut, QKeySequence
from qt_compat.QtWidgets import (QWidget, QVBoxLayout, QHBoxLayout, QLabel, QPushButton,
                               QCheckBox, QSpinBox, QDoubleSpinBox, QTableWidget, QTableWidgetItem,
                               QHeaderView, QAbstractItemView, QMessageBox)
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
        title = QLabel("键盘鼠标录制")
        title.setObjectName("pageTitle")
        layout.addWidget(title)
        tip = QLabel("记录鼠标移动、双击、拖拽、侧键、双向滚轮及键盘按下/松开（含组合键、功能键、数字小键盘和媒体键）。\n"
                     "仅点击开始后监听。不要录入密码等敏感信息；录制结果保存在当前任务中。\n"
                     "Esc 或停止按钮均可结束录制；默认也可按 F8。要录制 F8 请取消下方选项。硬件 Fn 等操作受系统限制。\n"
                     "macOS 需辅助功能/输入监控权限；Linux 需 X11。原始系统键码应在同一系统回放。")
        tip.setWordWrap(True)
        tip.setObjectName("mutedText")
        layout.addWidget(tip)
        options = QHBoxLayout()
        options.addWidget(QLabel("开始倒计时（秒）"))
        self.delay = QSpinBox()
        self.delay.setRange(1, 10)
        self.delay.setValue(3)
        options.addWidget(self.delay)
        self.f8_option = QCheckBox("F8 停止录制")
        self.f8_option.setChecked(True)
        options.addWidget(self.f8_option)
        self.hide_option = QCheckBox("录制时隐藏主窗口")
        self.hide_option.setChecked(True)
        self.timing_option = QCheckBox("保留操作时间间隔")
        self.timing_option.setChecked(True)
        self.connect_option = QCheckBox("自动连接录制流程")
        self.connect_option.setChecked(True)
        self.auto_option = QCheckBox("停止后自动写入（原速）")
        self.auto_option.setChecked(False)
        self.auto_option.setToolTip("默认停止后预览，再选择原速或倍速写入；勾选后自动按原速写入。")
        layout.addLayout(options)
        options = QHBoxLayout()
        for option in (self.hide_option, self.timing_option, self.connect_option, self.auto_option):
            options.addWidget(option)
        options.addStretch()
        layout.addLayout(options)
        controls = QHBoxLayout()
        self.start_button = QPushButton("开始录制")
        self.start_button.setObjectName("accentButton")
        self.stop_button = QPushButton("停止录制（Esc / F8）")
        self.stop_button.setObjectName("dangerButton")
        self.write_button = QPushButton("写入表格与流程图")
        self.speed = QDoubleSpinBox()
        self.speed.setRange(0.1, 10.0)
        self.speed.setDecimals(2)
        self.speed.setSingleStep(0.25)
        self.speed.setValue(1.25)
        self.speed.setSuffix(" ×")
        self.speed.setMinimumWidth(95)
        self.speed.setToolTip("自定义 0.10–10.00 倍速；1.25 倍将 10 秒录制缩短至 8 秒。需保留操作时间间隔。")
        self.speed_write_button = QPushButton("按倍速（1.25）写入表格与流程图")
        self.speed.valueChanged.connect(lambda value: self.speed_write_button.setText(
            f"按倍速（{value:g}）写入表格与流程图"))
        self.speed_write_button.clicked.connect(self.write_at_speed)
        self.clear_button = QPushButton("清空录制预览")
        self.start_button.clicked.connect(self.begin)
        self.stop_button.clicked.connect(self.finish)
        self.escape_shortcut = QShortcut(QKeySequence("Esc"), self)
        self.escape_shortcut.activated.connect(self.finish)
        self.write_button.clicked.connect(lambda: self.write())
        self.clear_button.clicked.connect(self.clear)
        for button in (self.start_button, self.stop_button, self.clear_button):
            controls.addWidget(button)
        controls.addStretch()
        layout.addLayout(controls)
        write_controls = QHBoxLayout()
        write_controls.addWidget(self.write_button)
        write_controls.addWidget(self.speed_write_button)
        write_controls.addWidget(self.speed)
        write_controls.addStretch()
        layout.addLayout(write_controls)
        self.f8_option.toggled.connect(self.update_stop_mode)
        self.status = QLabel("未录制 · 鼠标移动每 10 毫秒采样，最多 20000 个事件；按键、点击及滚轮不降采样")
        self.status.setWordWrap(True)
        self.status.setObjectName("taskStats")
        layout.addWidget(self.status)
        self.preview = QTableWidget(0, 3)
        self.preview.setHorizontalHeaderLabels(["序号", "指令", "参数"])
        self.preview.setEditTriggers(QAbstractItemView.EditTrigger.NoEditTriggers)
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
        self.write_button.setEnabled(not self.busy and bool(self.drafts) and not self.written)
        self.speed_write_button.setEnabled(self.write_button.isEnabled())
        self.speed.setEnabled(not self.busy and not self.written)
        self.clear_button.setEnabled(not self.busy and bool(self.drafts))
        for control in (self.delay, self.f8_option, self.hide_option, self.timing_option, self.connect_option, self.auto_option):
            control.setEnabled(not self.busy)
        self.hide_option.setEnabled(not self.busy and self.f8_option.isChecked())

    def update_stop_mode(self, enabled):
        if not enabled:
            self.hide_option.setChecked(False)
        self.stop_button.setText("停止录制（Esc / F8）" if enabled else "停止录制（Esc）")
        self.update_buttons()

    def begin(self):
        if getattr(self.window, '_update_preparing', False):
            self.status.setText('正在准备更新，暂时无法开始录制。')
            return
        if self.busy:
            return
        if self.window.command_thread.isRunning():
            QMessageBox.warning(self, "无法录制", "请先停止正在运行的任务。")
            return
        if self.drafts and not self.written and QMessageBox.question(
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
                    stop_with_f8=self.f8_option.isChecked())
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
                self.status.setText(f"录制中 · {len(self.buffer.snapshot())} 个事件 · {stop_tip}")

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
            self.drafts = events_to_drafts(self.buffer.snapshot(), self.timing_option.isChecked())
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
        if self.window.command_thread.isRunning():
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
