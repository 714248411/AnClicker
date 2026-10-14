"""Frozen bound-client screenshots with lossless crop and client-coordinate picking."""
from dataclasses import dataclass
from types import SimpleNamespace
from qt_compat.QtCore import Qt, QRect, QRectF, Signal
from qt_compat.QtGui import QImage, QPainter, QPen
from qt_compat.QtWidgets import (QWidget, QDialog, QLabel, QPushButton, QVBoxLayout,
    QHBoxLayout, QDialogButtonBox, QSizePolicy)
from qt_compat import BINDING
if BINDING == 'PySide2':
    from shiboken2 import isValid
else:
    from shiboken6 import isValid


def binding_parameters(editor, required=False):
    context = getattr(editor, 'context', None)
    callback = getattr(context, 'metadata', {}).get('previous_background_binding')
    parameters = callback() if callable(callback) else None
    if parameters is None and required:
        raise ValueError('请先在这条指令上方添加并连接“绑定选择窗口”，再使用后台截图。')
    return parameters


@dataclass
class CaptureSelection:
    image: object
    region: tuple
    point: tuple
    color: tuple

    def save_selection(self, path):
        self.image.save(str(path))


class CaptureCanvas(QWidget):
    changed = Signal()

    def __init__(self, image, mode='region', parent=None):
        super().__init__(parent)
        self.image = image.convert('RGB')
        self.mode = mode
        raw = self.image.tobytes()
        self.background = QImage(raw, self.image.width, self.image.height,
                                 self.image.width * 3, QImage.Format.Format_RGB888).copy()
        self.view = QRect(0, 0, self.image.width, self.image.height)
        self.selection = QRect()
        self.point = None
        self.anchor = None
        self.setMinimumSize(280, 200)
        self.setSizePolicy(QSizePolicy.Expanding, QSizePolicy.Expanding)
        self.setCursor(Qt.CrossCursor)

    def image_rect(self):
        scale = min(max(1, self.width()-20)/self.view.width(),
                    max(1, self.height()-20)/self.view.height())
        width, height = self.view.width()*scale, self.view.height()*scale
        return QRectF((self.width()-width)/2, (self.height()-height)/2, width, height)

    def client_point(self, position, clamp=False):
        rect = self.image_rect()
        if not clamp and not rect.contains(position):
            return None
        x = min(self.view.width()-1, max(0, int((position.x()-rect.x())*self.view.width()/rect.width())))
        y = min(self.view.height()-1, max(0, int((position.y()-rect.y())*self.view.height()/rect.height())))
        return self.view.x()+x, self.view.y()+y

    def crop_view(self):
        if not self.selection.isEmpty():
            self.view = QRect(self.selection)
            self.selection = QRect()
            self.point = None
            self.changed.emit()
            self.update()

    def reset_view(self):
        self.view = QRect(0, 0, self.image.width, self.image.height)
        self.selection = QRect()
        self.point = None
        self.changed.emit()
        self.update()

    def mousePressEvent(self, event):
        if event.button() != Qt.LeftButton:
            return
        point = self.client_point(event.position())
        if point is None:
            return
        self.anchor = point
        self.point = point
        self.selection = QRect(*point, 1, 1)
        self.changed.emit()
        self.update()

    def mouseMoveEvent(self, event):
        if self.anchor is None or self.mode == 'point':
            return
        point = self.client_point(event.position(), clamp=True)
        x, y = min(point[0], self.anchor[0]), min(point[1], self.anchor[1])
        self.selection = QRect(x, y, abs(point[0]-self.anchor[0])+1, abs(point[1]-self.anchor[1])+1)
        self.point = (x+self.selection.width()//2, y+self.selection.height()//2)
        self.changed.emit()
        self.update()

    def mouseReleaseEvent(self, event):
        if event.button() == Qt.LeftButton and self.anchor is not None:
            self.mouseMoveEvent(event)
            self.anchor = None

    def paintEvent(self, event):
        painter = QPainter(self)
        painter.fillRect(self.rect(), self.palette().window())
        rect = self.image_rect()
        painter.drawImage(rect, self.background, QRectF(self.view))
        sx, sy = rect.width()/self.view.width(), rect.height()/self.view.height()
        painter.setPen(QPen(self.palette().highlight().color(), 2))
        if self.mode == 'region' and not self.selection.isEmpty():
            painter.drawRect(QRectF(rect.x()+(self.selection.x()-self.view.x())*sx,
                rect.y()+(self.selection.y()-self.view.y())*sy,
                self.selection.width()*sx, self.selection.height()*sy))
        if self.point is not None:
            x = rect.x()+(self.point[0]-self.view.x()+.5)*sx
            y = rect.y()+(self.point[1]-self.view.y()+.5)*sy
            painter.drawLine(int(x)-8, int(y), int(x)+8, int(y))
            painter.drawLine(int(x), int(y)-8, int(x), int(y)+8)

    def result(self):
        if self.point is None:
            return None
        r = self.selection
        region = (r.x(), r.y(), r.width(), r.height())
        return CaptureSelection(self.image.crop((r.x(), r.y(), r.x()+r.width(), r.y()+r.height())),
                                region, self.point, self.image.getpixel(self.point))


class BackgroundCaptureDialog(QDialog):
    def __init__(self, image, mode='region', parent=None):
        super().__init__(parent)
        self.setWindowTitle('后台窗口快速截图' if mode=='region' else '从后台窗口截图取点')
        self.resize(900, 650)
        self.setMinimumSize(420, 360)
        layout = QVBoxLayout(self)
        hint = QLabel('在窗口截图中拖动框选，可在选区内再次截图。' if mode=='region' else '单击窗口截图选择坐标和颜色，点击“使用坐标”确认。')
        hint.setWordWrap(True)
        layout.addWidget(hint)
        info = QLabel('坐标以原窗口内容区左上角为 0,0；预览缩放不改变坐标。预览选点不会点击目标窗口。')
        info.setWordWrap(True)
        layout.addWidget(info)
        self.canvas = CaptureCanvas(image, mode, self)
        layout.addWidget(self.canvas, 1)
        self.status = QLabel('请先选择截图区域。' if mode=='region' else '请先选择坐标。')
        self.status.setWordWrap(True)
        layout.addWidget(self.status)
        row = QHBoxLayout()
        self.crop_button = QPushButton('在选区内再次截图')
        self.reset_button = QPushButton('返回完整窗口截图')
        for button in (self.crop_button, self.reset_button):
            button.setAutoDefault(False)
            button.setVisible(mode=='region')
            row.addWidget(button)
        layout.addLayout(row)
        self.buttons = QDialogButtonBox(QDialogButtonBox.Ok | QDialogButtonBox.Cancel)
        self.buttons.button(QDialogButtonBox.Ok).setText('使用截图' if mode=='region' else '使用坐标')
        self.buttons.button(QDialogButtonBox.Cancel).setText('取消')
        self.buttons.accepted.connect(self.accept)
        self.buttons.rejected.connect(self.reject)
        layout.addWidget(self.buttons)
        self.crop_button.clicked.connect(self.canvas.crop_view)
        self.reset_button.clicked.connect(self.canvas.reset_view)
        self.canvas.changed.connect(self._changed)
        self._changed()

    def _changed(self):
        valid = self.canvas.point is not None
        self.buttons.button(QDialogButtonBox.Ok).setEnabled(valid)
        self.crop_button.setEnabled(valid and self.canvas.selection.width()>1 and self.canvas.selection.height()>1)
        if valid:
            x,y = self.canvas.point
            r = self.canvas.selection
            self.status.setText(f'窗口坐标：{x},{y}；选区：{r.x()},{r.y()},{r.width()},{r.height()}；RGB：{self.canvas.image.getpixel((x,y))}')
        else:
            self.status.setText('请在当前窗口截图中选择。')

    def accept(self):
        if self.canvas.point is not None:
            super().accept()


class _CaptureOperation:
    image = None

    def __init__(self, parameters):
        self.parameters = parameters

    def execute(self, context, command):
        from background_runtime import bind_background, current_backend
        from instructions.common.actions import substitute_variables
        parameters = {key: substitute_variables(context, value) if isinstance(value,str) else value
                      for key, value in self.parameters.items()}
        bind_background(context, parameters)
        backend = current_backend(context)
        image = backend.screenshot()
        if tuple(backend.size()) != image.size:
            raise RuntimeError('截图期间窗口大小发生变化，请保持窗口尺寸稳定后重新截图。')
        self.image = image


def capture_window(editor, parameters):
    from background_binding import capture_enabled
    from instructions.models import ExecutionContext
    from instructions.common.test_runner import CancellableTestDialog
    from settings_theme import apply_settings_theme
    if not capture_enabled(parameters):
        raise ValueError('请先在“绑定选择窗口”中开启“启用截图 / 识图 / 取色”，再使用后台快速截图。')
    source = getattr(editor, 'context', None) or ExecutionContext()
    context = ExecutionContext(variables=dict(source.variables), services=source.services)
    operation = _CaptureOperation(dict(parameters))
    spec = SimpleNamespace(display_name='后台窗口截图', create_executor=lambda: operation)
    # The helper owns its context/transport; never borrow the running flow's session.
    def cancel(*_):
        context.stop_requested = True
    editor.destroyed.connect(cancel)
    editor.finished.connect(cancel)
    progress = CancellableTestDialog(spec, None, context)
    apply_settings_theme(progress, source.metadata.get('main_window'))
    try:
        progress.exec()
        if context.stop_requested:
            return None
        if progress.worker.error is not None:
            raise progress.worker.error
        return operation.image
    finally:
        progress.deleteLater()
        if isValid(editor):
            editor.destroyed.disconnect(cancel)
            editor.finished.disconnect(cancel)


def select_background(editor, parameters, mode='region'):
    metadata = getattr(getattr(editor, 'context', None), 'metadata', {})
    host = metadata.get('main_window')
    workspace = getattr(host, 'workspace', None)
    thread = getattr(host, 'command_thread', None)
    view = getattr(host, 'view_workspace', None)
    scheduler = getattr(host, 'task_scheduler', None)
    if (getattr(editor, '_background_capture_active', False)
            or getattr(workspace, '_instruction_test_active', False)
            or (thread is not None and thread.isRunning())
            or getattr(scheduler, 'busy', False)
            or getattr(host, '_update_preparing', False)
            or (view is not None and (view.recording_page.busy or view.web_recording_page.busy))):
        raise RuntimeError('请先停止运行、录制或其他测试，再进行后台截图。')
    was_visible = editor.isVisible()
    editor._background_capture_active = True
    if workspace is not None:
        workspace._instruction_test_active = True
    buttons = editor.ui.buttonBox
    enabled = buttons.isEnabled()
    buttons.setEnabled(False)
    dialog = None
    try:
        image = capture_window(editor, parameters)
        if image is None or not isValid(editor) or (was_visible and not editor.isVisible()):
            return None
        dialog = BackgroundCaptureDialog(image, mode)
        from settings_theme import apply_settings_theme
        apply_settings_theme(dialog, host)
        editor.finished.connect(dialog.reject)
        editor.destroyed.connect(dialog.reject)
        if dialog.exec() == QDialog.Accepted and isValid(editor) and (not was_visible or editor.isVisible()):
            return dialog.canvas.result()
        return None
    finally:
        if workspace is not None:
            workspace._instruction_test_active = False
        if dialog is not None:
            if isValid(editor):
                editor.finished.disconnect(dialog.reject)
                editor.destroyed.disconnect(dialog.reject)
            dialog.deleteLater()
        if isValid(editor):
            editor._background_capture_active = False
            buttons.setEnabled(enabled)


def save_capture(editor, selection, folder=None, suffix='.png'):
    from functions import IMAGES_FOLDER
    from smart_capture import capture_path
    path = capture_path(folder or IMAGES_FOLDER).with_suffix(suffix)
    selection.save_selection(path)
    callback = getattr(getattr(editor, 'context', None), 'metadata', {}).get('remember_capture')
    if callable(callback):
        callback(str(path))
    return path
