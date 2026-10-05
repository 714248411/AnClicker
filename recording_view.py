"""Visible, opt-in recording workspace; never installs hooks during startup."""
import json
import time
import sys

from PySide6.QtCore import Signal, QTimer
from PySide6.QtWidgets import (QWidget, QVBoxLayout, QHBoxLayout, QLabel, QPushButton,
                               QCheckBox, QSpinBox, QTableWidget, QTableWidgetItem,
                               QHeaderView, QAbstractItemView, QMessageBox)
from input_recording import RecordingBuffer, GlobalInputRecorder, events_to_drafts


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
        tip = QLabel("记录鼠标移动、点击、拖拽、滚轮及键盘按下/松开；按 F8 停止。\n"
                     "仅点击开始后监听。不要录入密码等敏感信息；录制结果保存在当前任务中。\n"
                     "macOS 需授予辅助功能/输入监控权限；Linux 需支持 X11 全局输入监听。")
        tip.setWordWrap(True)
        tip.setObjectName("mutedText")
        layout.addWidget(tip)
        options = QHBoxLayout()
        options.addWidget(QLabel("开始倒计时（秒）"))
        self.delay = QSpinBox()
        self.delay.setRange(1, 10)
        self.delay.setValue(3)
        options.addWidget(self.delay)
        self.hide_option = QCheckBox("录制时隐藏主窗口")
        self.hide_option.setChecked(True)
        self.timing_option = QCheckBox("保留操作时间间隔")
        self.timing_option.setChecked(True)
        self.connect_option = QCheckBox("自动连接录制流程")
        self.connect_option.setChecked(True)
        self.auto_option = QCheckBox("停止后自动写入")
        self.auto_option.setChecked(True)
        for option in (self.hide_option, self.timing_option, self.connect_option, self.auto_option):
            options.addWidget(option)
        options.addStretch()
        layout.addLayout(options)
        controls = QHBoxLayout()
        self.start_button = QPushButton("开始录制")
        self.start_button.setObjectName("accentButton")
        self.stop_button = QPushButton("停止录制（F8）")
        self.stop_button.setObjectName("dangerButton")
        self.write_button = QPushButton("写入表格与流程图")
        self.clear_button = QPushButton("清空录制预览")
        self.start_button.clicked.connect(self.begin)
        self.stop_button.clicked.connect(self.finish)
        self.write_button.clicked.connect(self.write)
        self.clear_button.clicked.connect(self.clear)
        for button in (self.start_button, self.stop_button, self.write_button, self.clear_button):
            controls.addWidget(button)
        controls.addStretch()
        layout.addLayout(controls)
        self.status = QLabel("未录制 · 每 50 毫秒最多采样一次鼠标移动，最多 2000 个事件")
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
        self.clear_button.setEnabled(not self.busy and bool(self.drafts))
        for control in (self.delay, self.hide_option, self.timing_option, self.connect_option, self.auto_option):
            control.setEnabled(not self.busy)

    def begin(self):
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
                self.status.setText(f"{max(1, int(remaining + 0.999))} 秒后开始 · 可点击停止取消")
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
                    self.exclude_mouse, self.exclude_keyboard)
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
                self.status.setText(self.status.text() + " · 达到 2000 事件上限，已自动停止")
            elif time.monotonic() - self.capture_started > 1 and any(
                    not listener.is_alive() for listener in self.recorder.listeners):
                self.failed("输入监听器已退出，请检查输入监听权限或桌面环境。")
            else:
                self.status.setText(f"录制中 · {len(self.buffer.snapshot())} 个事件 · 按 F8 停止")

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

    def write(self):
        if self.busy or not self.drafts or self.written:
            return
        if self.window.command_thread.isRunning():
            QMessageBox.warning(self, "无法写入", "请先停止正在运行的任务。")
            return
        try:
            workspace = self.window.workspace
            ids = workspace.repository.append_recording(self.drafts, connect=self.connect_option.isChecked())
            self.written = True  # Never insert a duplicate if projection refresh fails.
            self.update_buttons()
            workspace.reload_graph()
            workspace.graphFinalized.emit(False)
            self.status.setText(f"已追加 {len(ids)} 条指令 · 表格、流程图与多功能已同步 · 未修改原有指令")
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
