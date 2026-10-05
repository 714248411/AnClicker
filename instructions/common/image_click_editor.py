"""旧版图像点击工作区，复用当前参数契约和应用主题。"""
from pathlib import Path
from datetime import datetime

from PySide6.QtCore import Qt, QRectF, Signal, QTimer, QUrl
from PySide6.QtGui import QPixmap, QPainter, QPen, QDesktopServices
from PySide6.QtWidgets import (
    QWidget, QLabel, QPushButton, QComboBox, QCheckBox, QSlider, QSpinBox,
    QDialog, QDialogButtonBox, QVBoxLayout, QHBoxLayout, QGridLayout,
    QGroupBox, QFileDialog, QMessageBox, QTabWidget, QSizePolicy,
)
from .editor import _RegionSelectionDialog
from . import actions


class ImagePositionCanvas(QWidget):
    position_changed = Signal(int, int)

    def __init__(self, pixmap, parent=None):
        super().__init__(parent)
        self.image = pixmap
        self.offset = (0, 0)
        self.setMinimumSize(260, 200)
        self.setSizePolicy(QSizePolicy.Policy.Expanding, QSizePolicy.Policy.Expanding)

    def image_rect(self):
        scale = min((self.width()-20)/self.image.width(),
                    (self.height()-20)/self.image.height(), 1.0)
        w, h = self.image.width()*scale, self.image.height()*scale
        return QRectF((self.width()-w)/2, (self.height()-h)/2, w, h)

    def paintEvent(self, event):
        painter = QPainter(self)
        rect = self.image_rect()
        painter.drawPixmap(rect, self.image, QRectF(self.image.rect()))
        painter.setPen(QPen(self.palette().highlight().color(), 2))
        x = rect.x() + (self.image.width()//2+self.offset[0])*rect.width()/self.image.width()
        y = rect.y() + (self.image.height()//2+self.offset[1])*rect.height()/self.image.height()
        painter.drawLine(int(rect.left()), int(y), int(rect.right()), int(y))
        painter.drawLine(int(x), int(rect.top()), int(x), int(rect.bottom()))

    def mousePressEvent(self, event):
        if event.button() == Qt.MouseButton.LeftButton:
            self.select_position(event.position())

    def mouseMoveEvent(self, event):
        if event.buttons() & Qt.MouseButton.LeftButton:
            self.select_position(event.position())

    def select_position(self, point):
        rect = self.image_rect()
        if not rect.contains(point):
            return
        x = min(self.image.width()-1, int((point.x()-rect.x())*self.image.width()/rect.width()))
        y = min(self.image.height()-1, int((point.y()-rect.y())*self.image.height()/rect.height()))
        self.offset = (x-self.image.width()//2, y-self.image.height()//2)
        self.position_changed.emit(*self.offset)
        self.update()


class ImagePositionDialog(QDialog):
    def __init__(self, path, value, parent=None):
        super().__init__(parent)
        self.setWindowTitle('调整点击位置')
        self.resize(640, 440)
        pixmap = QPixmap(str(path))
        if pixmap.isNull():
            raise ValueError('无法读取图像，请先选择有效的图片。')
        layout = QVBoxLayout(self)
        layout.addWidget(QLabel('在图片中单击或拖动十字线；偏移以图片中心为 (0,0)。'))
        self.canvas = ImagePositionCanvas(pixmap, self)
        layout.addWidget(self.canvas, 1)
        row = QHBoxLayout()
        self.x = QSpinBox(); self.y = QSpinBox()
        for spin in (self.x, self.y):
            spin.setRange(-1000000, 1000000)
        self.random = QCheckBox('图像内随机位置')
        center = QPushButton('恢复中心')
        for widget in (QLabel('X'), self.x, QLabel('Y'), self.y, self.random, center):
            row.addWidget(widget)
        layout.addLayout(row)
        self.canvas.position_changed.connect(self.set_offset)
        self.x.valueChanged.connect(self.update_offset)
        self.y.valueChanged.connect(self.update_offset)
        self.random.toggled.connect(self.toggle_random)
        center.clicked.connect(lambda: self.set_offset(0, 0))
        if '随机' in str(value):
            self.random.setChecked(True)
        else:
            self.set_offset(*actions.point(value or '(0,0)'))
        buttons = QDialogButtonBox(QDialogButtonBox.StandardButton.Ok | QDialogButtonBox.StandardButton.Cancel)
        buttons.button(QDialogButtonBox.StandardButton.Ok).setText('确定')
        buttons.button(QDialogButtonBox.StandardButton.Cancel).setText('取消')
        buttons.accepted.connect(self.accept); buttons.rejected.connect(self.reject)
        layout.addWidget(buttons)

    def set_offset(self, x, y):
        self.x.setValue(x); self.y.setValue(y)

    def update_offset(self):
        self.canvas.offset = (self.x.value(), self.y.value())
        self.canvas.update()

    def toggle_random(self, checked):
        for widget in (self.x, self.y, self.canvas):
            widget.setEnabled(not checked)

    def value(self):
        return '(随机,随机)' if self.random.isChecked() else f'({self.x.value()},{self.y.value()})'


class ImageClickEditorMixin:
    """保留生成式 UI 的参数控件，以便旧文件和注册表保持兼容。"""

    def __init__(self, parent=None, draft=None, context=None):
        super().__init__(parent, draft=None, context=context)
        self.db = self._variable_database()
        self._build_image_workspace()
        if draft is not None:
            self.load_draft(draft)

    def _build_image_workspace(self):
        ui = self.ui
        old = ui.parameterGroupBox
        panel = QWidget()
        panel.setObjectName('imageClickWorkspace')
        layout = QVBoxLayout(panel)
        layout.setContentsMargins(0, 0, 0, 0)
        hint = QLabel('操作说明：将图像统一保存至资源文件夹，添加文件夹后即可选择。')
        hint.setWordWrap(True); hint.setAlignment(Qt.AlignmentFlag.AlignCenter)
        layout.addWidget(hint)
        self.folder_label = QLabel(); self.folder_label.setWordWrap(True)
        self.folder_label.setAlignment(Qt.AlignmentFlag.AlignCenter)
        layout.addWidget(self.folder_label)
        row = QHBoxLayout()
        self.capture_button = QPushButton('快捷截图')
        self.capture_button.setObjectName('accentButton')
        self.open_folder_button = QPushButton('打开资源文件夹')
        row.addWidget(self.capture_button); row.addWidget(self.open_folder_button)
        layout.addLayout(row)
        grid = QGridLayout()
        self.folder_combo = QComboBox(); self.folder_combo.setEditable(True)
        self.image_combo = QComboBox(); self.image_combo.setEditable(True)
        self.add_folder_button = QPushButton('添加文件夹')
        ui.auxiliary_0.setText('选择图片')
        self.advanced_button = QPushButton('高级设置')
        grid.addWidget(QLabel('文件夹名称：'), 0, 0)
        grid.addWidget(self.folder_combo, 0, 1, 1, 2)
        grid.addWidget(self.add_folder_button, 0, 3)
        grid.addWidget(QLabel('图像名称：'), 1, 0)
        grid.addWidget(self.image_combo, 1, 1)
        grid.addWidget(ui.auxiliary_0, 1, 2)
        ui.parameter_4.setText('启用灰度识别')
        grid.addWidget(ui.parameter_4, 1, 3)
        grid.addWidget(QLabel('指令名称：'), 2, 0)
        grid.addWidget(ui.parameter_1, 2, 1, 1, 2)
        grid.addWidget(self.advanced_button, 2, 3)
        grid.setColumnStretch(1, 1)
        layout.addLayout(grid)
        columns = QHBoxLayout()
        click = QGroupBox('图像点击位置和精度'); left = QGridLayout(click)
        ui.auxiliary_6.setText('调整点击位置')
        left.addWidget(ui.parameter_6, 0, 0); left.addWidget(ui.auxiliary_6, 0, 1)
        self.confidence_slider = QSlider(Qt.Orientation.Horizontal)
        self.confidence_slider.setObjectName('imageConfidenceSlider')
        self.confidence_slider.setRange(1, 100); self.confidence_slider.setValue(80)
        self.confidence_label = QLabel('80%')
        left.addWidget(QLabel('识别精度：'), 1, 0)
        left.addWidget(self.confidence_slider, 1, 1); left.addWidget(self.confidence_label, 1, 2)
        self.region_group = QGroupBox('启用指定区域识别')
        self.region_group.setCheckable(True); self.region_group.setChecked(False)
        right = QVBoxLayout(self.region_group)
        ui.parameter_3.setPlaceholderText('(x,y,宽度,高度)')
        ui.auxiliary_3.setText('设置区域')
        right.addWidget(ui.parameter_3); right.addWidget(ui.auxiliary_3)
        columns.addWidget(click, 1); columns.addWidget(self.region_group, 1)
        layout.addLayout(columns)
        missing = QHBoxLayout()
        self.skip_check = QCheckBox('未找到图像时自动略过'); self.skip_check.setChecked(True)
        self.timeout_spin = QSpinBox(); self.timeout_spin.setRange(0, 86400); self.timeout_spin.setValue(10)
        self.timeout_spin.setSuffix(' 秒'); self.timeout_spin.setEnabled(False)
        missing.addWidget(self.skip_check); missing.addWidget(QLabel('否则等待：')); missing.addWidget(self.timeout_spin)
        missing.addStretch(); layout.addLayout(missing)
        self.preview = QLabel('请选择图片'); self.preview.setAlignment(Qt.AlignmentFlag.AlignCenter)
        self.preview.setMinimumHeight(100)
        self.preview.setSizePolicy(QSizePolicy.Policy.Ignored, QSizePolicy.Policy.Preferred)
        self.tabs = QTabWidget()
        self.tabs.addTab(ui.commonGroupBox, '功能参数'); self.tabs.addTab(self.preview, '图像预览')
        ui.rootLayout.replaceWidget(old, panel)
        ui.rootLayout.insertWidget(2, self.tabs)
        # Serialized backing fields remain alive; visible controls above edit them.
        for control in (ui.parameter_0, ui.parameter_2, ui.parameter_5):
            control.setParent(panel); control.hide()
        old.hide(); old.deleteLater()
        self.folder_combo.currentTextChanged.connect(self._refresh_image_names)
        self.image_combo.currentTextChanged.connect(self._select_image)
        self.capture_button.clicked.connect(lambda: self._select_screen(True))
        self.open_folder_button.clicked.connect(self._open_folder)
        self.add_folder_button.clicked.connect(self._add_folder)
        self.advanced_button.clicked.connect(self._advanced_settings)
        self.confidence_slider.valueChanged.connect(self._set_confidence)
        ui.parameter_5.valueChanged.connect(self._reflect_confidence)
        self.skip_check.toggled.connect(self._set_missing_policy)
        self.timeout_spin.valueChanged.connect(self._set_missing_policy)
        folders = self.db.extract_resource_folder_path()
        self.folder_combo.addItems(folders)
        for button in panel.findChildren(QPushButton):
            button.setMinimumHeight(32)
        for combo in (self.folder_combo, self.image_combo):
            combo.setMinimumContentsLength(8)
            combo.setSizeAdjustPolicy(QComboBox.SizeAdjustPolicy.AdjustToMinimumContentsLengthWithIcon)
        self.resize(760, 700)

    def _set_confidence(self, value):
        self.ui.parameter_5.setValue(value / 100)
        self.confidence_label.setText(f'{value}%')

    def _reflect_confidence(self, value):
        self.confidence_slider.setValue(round(value * 100))

    def _set_missing_policy(self, *_):
        self.timeout_spin.setEnabled(not self.skip_check.isChecked())
        self.ui.parameter_2.setText('自动略过' if self.skip_check.isChecked() else str(self.timeout_spin.value()))

    def _refresh_image_names(self, folder):
        self.folder_label.setText(f'当前文件夹：\n{folder}')
        self.folder_label.setToolTip(folder)
        self.image_combo.clear()
        path = Path(folder)
        try:
            names = sorted(p.name for p in path.iterdir() if p.is_file() and p.suffix.lower() in {'.png', '.jpg', '.jpeg', '.bmp', '.webp'}) if folder and path.is_dir() else []
        except OSError:
            names = []
        self.image_combo.addItems(names)
        self._select_image(self.image_combo.currentText())

    def _select_image(self, name):
        path = str(Path(self.folder_combo.currentText()) / name) if name else ''
        self.ui.parameter_0.setText(path)
        pixmap = QPixmap(path) if path else QPixmap()
        if pixmap.isNull():
            self.preview.setText('请选择有效图片')
        else:
            self.preview.setPixmap(pixmap.scaled(560, 160, Qt.AspectRatioMode.KeepAspectRatio, Qt.TransformationMode.SmoothTransformation))

    def _set_image_path(self, path):
        path = Path(path)
        self.folder_combo.setCurrentText(str(path.parent))
        self.image_combo.setCurrentText(path.name)

    def _add_folder(self):
        folder = QFileDialog.getExistingDirectory(self, '添加资源文件夹', self.folder_combo.currentText())
        if folder:
            self.db.writes_to_resource_folder_path(folder)
            if self.folder_combo.findText(folder) < 0:
                self.folder_combo.addItem(folder)
            self.folder_combo.setCurrentText(folder)

    def _open_folder(self):
        folder = self.folder_combo.currentText()
        if not folder or not Path(folder).is_dir():
            QMessageBox.warning(self, '资源文件夹', '文件夹不存在，请先添加有效文件夹。')
        elif not QDesktopServices.openUrl(QUrl.fromLocalFile(folder)):
            QMessageBox.warning(self, '资源文件夹', '无法打开文件夹。')

    def _advanced_settings(self):
        from WindowControl.设置窗口 import Setting
        dialog = Setting(self)
        dialog.tabWidget.setCurrentIndex(0)
        dialog.exec()

    def _run_auxiliary(self, key):
        if key == '图像路径':
            path, _ = QFileDialog.getOpenFileName(self, '选择图片', self.folder_combo.currentText(), '图像 (*.png *.jpg *.jpeg *.bmp *.webp)')
            if path:
                self._set_image_path(path)
        elif key == '点击位置':
            try:
                dialog = ImagePositionDialog(self.ui.parameter_0.text(), self.ui.parameter_6.text(), self)
                if dialog.exec() == QDialog.DialogCode.Accepted:
                    self.ui.parameter_6.setText(dialog.value())
            except ValueError as error:
                QMessageBox.warning(self, '点击位置', str(error))
        elif key == '区域':
            self._select_screen(False)
        else:
            super()._run_auxiliary(key)

    def _select_screen(self, capture):
        if capture and (not self.folder_combo.currentText() or not Path(self.folder_combo.currentText()).is_dir()):
            QMessageBox.warning(self, '快捷截图', '请先选择有效资源文件夹。')
            return
        host = self.parentWidget().window() if self.parentWidget() else None
        host_visible = host is not None and host.isVisible()
        self.hide()
        if host_visible:
            host.hide()
        def restore():
            if host_visible:
                host.show()
            self.show(); self.raise_(); self.activateWindow()
        def choose():
            selector = _RegionSelectionDialog()
            selector.exec()
            region = selector.selected_region()
            selector.deleteLater()
            def finish():
                try:
                    if region and capture:
                        path = Path(self.folder_combo.currentText()) / f'截图_{datetime.now():%Y%m%d_%H%M%S_%f}.png'
                        actions.pyautogui_module().screenshot(region=region).save(str(path))
                        self._refresh_image_names(str(path.parent))
                        self._set_image_path(path)
                    elif region:
                        self.ui.parameter_3.setText(str(region))
                        self.region_group.setChecked(True)
                except Exception as error:
                    QMessageBox.warning(self, '截图/区域设置失败', str(error))
                finally:
                    restore()
            QTimer.singleShot(180, finish)
        QTimer.singleShot(180, choose)

    def load_draft(self, draft):
        super().load_draft(draft)
        if not hasattr(self, 'folder_combo'):
            return
        path = self.ui.parameter_0.text()
        if path:
            self._set_image_path(path)
        region = self.ui.parameter_3.text()
        self.region_group.setChecked(region.replace(' ', '') not in ('', '(0,0,0,0)', '0,0,0,0'))
        policy = self.ui.parameter_2.text()
        if policy not in ('自动略过', '自动跳过', ''):
            try:
                self.timeout_spin.setValue(int(float(policy)))
            except ValueError:
                pass
            self.skip_check.setChecked(False)
        else:
            self.skip_check.setChecked(True)
        self._set_missing_policy()

    def get_draft(self):
        # Disabled region retains its coordinates for toggling back, but is not executed.
        control = self.ui.parameter_3
        saved = control.text()
        if not self.region_group.isChecked():
            control.setText('')
        try:
            draft = super().get_draft()
            if self.region_group.isChecked() and actions.region(saved) is None:
                raise ValueError('请先设置有效识别区域。')
            return draft
        finally:
            control.setText(saved)

    def _valid_image(self):
        path = self.ui.parameter_0.text()
        if not path or not Path(path).is_file() or QPixmap(path).isNull():
            QMessageBox.warning(self, '图像文件无效', '图像文件不存在或无法读取，请重新选择图片。')
            return False
        return True

    def _accept_if_valid(self):
        if self._valid_image():
            super()._accept_if_valid()

    def _test_if_valid(self):
        if self._valid_image():
            super()._test_if_valid()
