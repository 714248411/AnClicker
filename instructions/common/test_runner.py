"""Modal, responsive test runner for instructions that wait for user input."""
from PySide6.QtCore import QThread, Signal, Slot, QTimer
from PySide6.QtWidgets import QDialog, QLabel, QPushButton, QVBoxLayout


class _TestWorker(QThread):
    message = Signal(str)

    def __init__(self, spec, command, context, parent):
        super().__init__(parent)
        self.spec, self.command, self.context = spec, command, context
        self.error = None

    def run(self):
        output = self.context.output
        self.context.output = self.message.emit
        try:
            self.spec.create_executor().execute(self.context, self.command)
        except Exception as error:
            self.error = error
        finally:
            self.context.output = output


class CancellableTestDialog(QDialog):
    def __init__(self, spec, command, context, parent=None):
        super().__init__(parent)
        self.setWindowTitle(f'测试：{spec.display_name}')
        self.setMinimumWidth(360)
        self.context = context
        layout = QVBoxLayout(self)
        self.message = QLabel(f'正在测试：{spec.display_name}…', self)
        self.message.setWordWrap(True)
        layout.addWidget(self.message)
        self.cancel_button = QPushButton('取消测试（Esc）', self)
        layout.addWidget(self.cancel_button)
        self.cancel_button.clicked.connect(self.reject)
        self.worker = _TestWorker(spec, command, context, self)
        self.worker.message.connect(self.message.setText)
        self.worker.finished.connect(self._finished)
        self._finished_safely = False
        QTimer.singleShot(0, self.worker.start)

    def done(self, result):
        if not self._finished_safely:
            self.context.stop_requested = True
            self.message.setText('正在取消测试并安全结束等待…')
            self.cancel_button.setEnabled(False)
            return
        super().done(result)

    def reject(self):
        self.done(QDialog.DialogCode.Rejected)

    def closeEvent(self, event):
        if not self._finished_safely:
            self.reject()
            event.ignore()
        else:
            super().closeEvent(event)

    @Slot()
    def _finished(self):
        self.worker.wait()
        self._finished_safely = True
        self.done(QDialog.DialogCode.Rejected if self.context.stop_requested
                  else QDialog.DialogCode.Accepted)


def run_cancellable_test(spec, command, context, parent):
    dialog = CancellableTestDialog(spec, command, context, parent)
    try:
        dialog.exec()
        if dialog.worker.error is not None:
            raise dialog.worker.error
    finally:
        dialog.deleteLater()
