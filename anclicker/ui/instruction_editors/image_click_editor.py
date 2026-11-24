"""旧版图像点击工作区，复用当前参数契约和应用主题。"""
from pathlib import Path
from anclicker.ui.region_preview import RegionPreview
from anclicker.domain.instructions import InstructionDraft
from anclicker.ui.background_window_picker import pick_background_window
from anclicker.ui.image_region_picker import pick_fixed_region
from anclicker.platform.image_region import window_region, region_in_bound_window
from anclicker.platform.image_paths import resolve_image_reference, store_image_reference
from anclicker.app.paths import IMAGES_FOLDER
from datetime import datetime

from anclicker.platform.qt_compat.QtCore import Qt, QRectF, Signal, QTimer, QUrl, QSignalBlocker
from anclicker.platform.qt_compat.QtGui import QPixmap, QPainter, QPen, QDesktopServices
from anclicker.platform.qt_compat.QtWidgets import (
    QApplication, QWidget, QLabel, QPushButton, QComboBox, QCheckBox, QSlider, QSpinBox,
    QDialog, QDialogButtonBox, QVBoxLayout, QHBoxLayout, QGridLayout,
    QGroupBox, QFileDialog, QMessageBox, QTabWidget, QSizePolicy,
)
from anclicker.ui.instruction_editors.editor import _RegionSelectionDialog
from anclicker.instructions.common import actions
from anclicker.ui.smart_capture import SmartCaptureDialog

from anclicker._imports import DeferredImports as _DeferredImports

# Dependencies declared here retain their existing on-demand loading boundaries.
_module_imports = _DeferredImports(globals(), {
    'open_advanced_timing': ('from', 'anclicker.ui.timing_dialog', ('open_advanced_timing',), 0),
    'BINDING': ('from', 'anclicker.platform.qt_compat', ('BINDING',), 0),
    'isValid': ('from', 'shiboken2', ('isValid',), 0),
    'isValid_2': ('from', 'shiboken6', ('isValid',), 0),
    'IMAGES_FOLDER': ('from', 'anclicker.app.paths', ('IMAGES_FOLDER',), 0),
    'binding_parameters_select_background_save_capture': ('from', 'anclicker.platform.background_capture', ('binding_parameters', 'select_background', 'save_capture'), 0),
})



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
        elif getattr(context, 'metadata', {}).get('recent_capture'):
            path = context.metadata['recent_capture']
            if Path(path).is_file():
                self._set_image_path(path)

    def _build_image_workspace(self):
        ui = self.ui
        old = ui.parameterGroupBox
        # Qt 5's replaceWidget does not retain a Python-owned replacement.
        # Give it its final QObject parent before replacing the old group.
        panel = QWidget(self)
        panel.setObjectName('imageClickWorkspace')
        layout = QVBoxLayout(panel)
        layout.setContentsMargins(0, 0, 0, 0)
        hint = QLabel('操作说明：将图像统一保存至资源文件夹，添加文件夹后即可选择。')
        hint.setWordWrap(True); hint.setAlignment(Qt.AlignmentFlag.AlignCenter)
        layout.addWidget(hint)
        self.folder_label = QLabel(); self.folder_label.setWordWrap(False)
        self.folder_label.setSizePolicy(QSizePolicy.Policy.Ignored, QSizePolicy.Policy.Preferred)
        self.folder_label.setAlignment(Qt.AlignmentFlag.AlignCenter)
        layout.addWidget(self.folder_label)
        row = QHBoxLayout()
        self.capture_button = QPushButton('快捷截图')
        self.capture_button.setObjectName('accentButton')
        self.capture_button.setToolTip('流程上方存在后台绑定时，从目标窗口截图中再次框选；否则截取屏幕。')
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
        ui.parameter_1.setToolTip("无操作：判断图片是否存在，不移动或点击鼠标。存在则继续下一步；未找到则进入异常处理或已连接的报错跳转。")
        grid.addWidget(self.advanced_button, 2, 3)
        grid.setColumnStretch(1, 1)
        layout.addLayout(grid)
        columns = QHBoxLayout()
        click = QGroupBox('图像点击位置和精度'); left = QGridLayout(click)
        ui.auxiliary_6.setText('调整点击位置')
        left.addWidget(ui.parameter_6, 0, 0, 1, 2)
        left.addWidget(ui.auxiliary_6, 4, 0, 1, 2)
        left.setColumnStretch(0, 1)
        ui.parameter_6.setMinimumWidth(0)
        self.confidence_slider = QSlider(Qt.Orientation.Horizontal)
        self.confidence_slider.setObjectName('imageConfidenceSlider')
        self.confidence_slider.setRange(1, 100); self.confidence_slider.setValue(80)
        self.confidence_label = QLabel('80%')
        left.addWidget(QLabel('识别精度:'), 1, 0)
        left.addWidget(self.confidence_label, 1, 1)
        self.confidence_label.setAlignment(Qt.AlignRight | Qt.AlignVCenter)
        self.confidence_slider.setMinimumWidth(0)
        self.confidence_slider.setSizePolicy(QSizePolicy.Expanding, QSizePolicy.Fixed)
        left.addWidget(self.confidence_slider, 2, 0, 1, 2)
        left.setRowStretch(3, 1)
        self.region_group = QGroupBox('启动区域识别1')
        self.follow_region_group = QGroupBox('启动区域识别2')
        for group in (self.region_group, self.follow_region_group):
            group.setCheckable(True); group.setChecked(False)
        right = QVBoxLayout(self.region_group)
        follow_layout = QVBoxLayout(self.follow_region_group)
        ui.parameter_3.setPlaceholderText('(x,y,宽度,高度)')
        self._region_target = None
        ui.auxiliary_3.setText('框选固定区域')
        ui.auxiliary_3.setToolTip('拖动框选；单击窗口则使用该窗口当前范围，之后保持固定。')
        self.follow_region_button = QPushButton('跟随窗口区域')
        self.follow_region_button.clicked.connect(self._pick_follow_region)
        self.region_hint = QLabel('未选择跟随窗口')
        self.region_hint.setWordWrap(True)
        fixed_hint = QLabel('拖动框选，或单击获取窗口当前范围')
        follow_hint = QLabel('点选窗口，每次识别时更新范围')
        for label in (fixed_hint, follow_hint):
            label.setWordWrap(True)
            label.setObjectName('mutedText')
        right.addWidget(fixed_hint); right.addWidget(ui.parameter_3); right.addStretch(1); right.addWidget(ui.auxiliary_3)
        follow_layout.addWidget(follow_hint); follow_layout.addWidget(self.region_hint); follow_layout.addStretch(1); follow_layout.addWidget(self.follow_region_button)
        self.region_group.toggled.connect(lambda checked: self._toggle_region_group(False, checked))
        self.follow_region_group.toggled.connect(lambda checked: self._toggle_region_group(True, checked))
        for column_layout in (left, right, follow_layout):
            column_layout.setProperty("preserveVerticalStretch", True)
            column_layout.setContentsMargins(10, 12, 10, 10)
            column_layout.setSpacing(6)
        region_buttons = (ui.auxiliary_6, ui.auxiliary_3, self.follow_region_button)
        button_height = max(32, *(button.sizeHint().height() for button in region_buttons))
        for button in region_buttons:
            button.setFixedHeight(button_height)
        for group in (click, self.region_group, self.follow_region_group):
            group.setMinimumWidth(0)
            group.setSizePolicy(QSizePolicy.Ignored, QSizePolicy.Preferred)
            columns.addWidget(group, 1)
        layout.addLayout(columns)
        missing = QHBoxLayout()
        self.skip_check = QCheckBox('未找到图像时自动略过'); self.skip_check.setChecked(True)
        self.timeout_spin = QSpinBox(); self.timeout_spin.setRange(0, 86400); self.timeout_spin.setValue(10)
        self.timeout_spin.setSuffix(' 秒'); self.timeout_spin.setEnabled(False)
        self.waiting_label = QLabel('否则等待：')
        missing.addWidget(self.skip_check); missing.addWidget(self.waiting_label); missing.addWidget(self.timeout_spin)
        missing.addStretch(); layout.addLayout(missing)
        self.detection_hint = QLabel('图片存在则继续下一步；等待后仍未找到，进入“功能参数”的异常处理；已连接报错跳转时走异常线。')
        self.detection_hint.setWordWrap(True)
        self.detection_hint.setObjectName("mutedText")
        layout.addWidget(self.detection_hint)
        self.preview = QLabel('请选择图片'); self.preview.setAlignment(Qt.AlignmentFlag.AlignCenter)
        self.preview.setMinimumHeight(100)
        self.preview.setSizePolicy(QSizePolicy.Policy.Ignored, QSizePolicy.Policy.Preferred)
        self.tabs = QTabWidget()
        self.tabs.addTab(ui.commonGroupBox, '功能参数'); self.tabs.addTab(self.preview, '图像预览')
        self.region_preview = RegionPreview(self)
        self.region_preview_page = QWidget(self)
        preview_layout = QVBoxLayout(self.region_preview_page)
        self.region_offset_box = QGroupBox('跟随窗口偏移')
        self.region_offset_box.setSizePolicy(QSizePolicy.Expanding, QSizePolicy.Fixed)
        offsets_layout = QGridLayout(self.region_offset_box)
        offsets_layout.setContentsMargins(8, 4, 8, 6)
        offsets_layout.setHorizontalSpacing(6)
        offsets_layout.setVerticalSpacing(3)
        self.region_offset_spins = []
        for index, label in enumerate(('左上角 X:', '左上角 Y:', '右下角 X:', '右下角 Y:')):
            spin = QSpinBox(self.region_offset_box)
            spin.setRange(-100000,100000); spin.setSuffix(' px')
            spin.setMinimumWidth(0)
            spin.setMaximumWidth(110)
            spin.setSizePolicy(QSizePolicy.Expanding, QSizePolicy.Fixed)
            offsets_layout.addWidget(QLabel(label),index//2,index%2*2)
            offsets_layout.addWidget(spin,index//2,index%2*2+1)
            spin.valueChanged.connect(self._region_offsets_changed)
            self.region_offset_spins.append(spin)
        self.region_screenshot_button = QPushButton('全屏截图预览')
        self.region_screenshot_button.clicked.connect(lambda: self._capture_region_preview(fullscreen=True))
        self.follow_screenshot_button = QPushButton('全屏截图预览', self.region_offset_box)
        self.follow_screenshot_button.clicked.connect(lambda: self._capture_region_preview(fullscreen=True))
        offsets_layout.addWidget(self.follow_screenshot_button, 0, 4, 2, 1, Qt.AlignVCenter)
        offsets_layout.setColumnStretch(1, 1)
        offsets_layout.setColumnStretch(3, 1)
        preview_layout.addWidget(self.region_screenshot_button)
        preview_layout.addWidget(self.region_offset_box)
        preview_layout.addWidget(self.region_preview,1)
        self.tabs.addTab(self.region_preview_page, '区域预览')
        self.tabs.currentChanged.connect(self._region_preview_tab_changed)
        self.region_preview.region_changed.connect(self._preview_region_changed)
        ui.parameter_3.textChanged.connect(self._update_region_preview)
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
        ui.parameter_1.currentTextChanged.connect(self._image_action_changed)
        self.skip_check.toggled.connect(self._set_missing_policy)
        self.timeout_spin.valueChanged.connect(self._set_missing_policy)
        folders = self.db.extract_resource_folder_path()
        self.folder_combo.addItems(folders)
        for button in panel.findChildren(QPushButton):
            button.setMinimumHeight(32)
        for combo in (self.folder_combo, self.image_combo):
            combo.setMinimumContentsLength(8)
            combo.setSizeAdjustPolicy(QComboBox.SizeAdjustPolicy.AdjustToMinimumContentsLengthWithIcon)
        self._image_action_changed()
        self._configure_region_columns()
        self.resize(760, 700)

    def _configure_region_columns(self):
        window_image = getattr(self, 'WINDOW_IMAGE', False)
        self.region_group.setVisible(not window_image)
        self.follow_region_group.setVisible(window_image or bool(self._region_target))
        if window_image:
            self.region_group.setChecked(False)
            self.follow_region_group.setCheckable(False)
            self.follow_region_group.setTitle('窗口识别区域')
            self.follow_region_button.setText('点选目标窗口')
            layout = self.follow_region_group.layout()
            layout.removeWidget(self.follow_region_button)
            layout.insertWidget(0, self.follow_region_button)
        else:
            self.region_group.setTitle('启动区域识别')

    def _set_confidence(self, value):
        self.ui.parameter_5.setValue(value / 100)
        self.confidence_label.setText(f'{value}%')

    def _reflect_confidence(self, value):
        self.confidence_slider.setValue(round(value * 100))

    def _image_action_changed(self, *_):
        detection = self.ui.parameter_1.currentText() == '无操作'
        if detection and (_ or self.ui.parameter_2.text() in ('自动略过', '自动跳过', '')):
            # Switching the action starts at one second, even if the previous
            # click action had a numeric timeout. Loading restores saved values
            # below, and its final no-argument refresh must not reset them.
            with QSignalBlocker(self.timeout_spin):
                self.timeout_spin.setValue(1)
        for widget in (self.ui.parameter_6, self.ui.auxiliary_6):
            widget.setEnabled(not detection)
        self._set_missing_policy()

    def _set_missing_policy(self, *_):
        detection = self.ui.parameter_1.currentText() == '无操作'
        self.skip_check.setVisible(not detection)
        self.detection_hint.setVisible(detection)
        self.waiting_label.setText('查找等待：' if detection else '否则等待：')
        self.timeout_spin.setEnabled(detection or not self.skip_check.isChecked())
        skip = self.skip_check.isChecked() and not detection
        self.ui.parameter_2.setText('自动略过' if skip else str(self.timeout_spin.value()))

    def _refresh_image_names(self, folder, select=True):
        self.folder_label.setText(f'当前文件夹：{folder}')
        self.folder_label.setToolTip(folder)
        previous = self.image_combo.currentText()
        path = Path(folder)
        try:
            names = sorted(p.name for p in path.iterdir() if p.is_file() and p.suffix.lower() in {'.png', '.jpg', '.jpeg', '.bmp', '.webp'}) if folder and path.is_dir() else []
        except OSError:
            names = []
        # Rebuilding the list must not publish its temporary first item as the
        # active instruction image. Commit the final visible selection once.
        with QSignalBlocker(self.image_combo):
            self.image_combo.clear()
            self.image_combo.addItems(names)
            if previous in names:
                self.image_combo.setCurrentText(previous)
        if select:
            self._select_image(self.image_combo.currentText())

    def _select_image(self, name):
        path = str(Path(self.folder_combo.currentText()) / name) if name else ''
        try:
            # Keep the source folder visible while browsing multiple images.
            # The stored reference and preview already point at the managed copy.
            self._apply_image_path(path)
        except (OSError, ValueError) as error:
            QMessageBox.warning(self, '图片导入失败', str(error))

    def _apply_image_path(self, path):
        """Publish one image to the stored parameter and the preview together."""
        path = store_image_reference(path, project_path=self._image_project_path(),
                                     resource_folders=self.db.extract_resource_folder_path())
        self.ui.parameter_0.setText(path)
        pixmap = QPixmap()
        if path:
            try:
                # QPixmap(filename) has an implicit filename cache. Reading
                # bytes also refreshes previews when that file was replaced.
                pixmap.loadFromData(Path(self._resolved_image_path(path)).read_bytes())
            except OSError:
                pass
        if pixmap.isNull():
            self.preview.setText('请选择有效图片')
        else:
            self.preview.setPixmap(pixmap.scaled(560, 160, Qt.AspectRatioMode.KeepAspectRatio, Qt.TransformationMode.SmoothTransformation))

    def _set_image_path(self, path):
        original = store_image_reference(path, project_path=self._image_project_path(),
                                         resource_folders=self.db.extract_resource_folder_path())
        path = Path(self._resolved_image_path(original))
        # Refresh even in the same folder (e.g. consecutive captures). Do not
        # temporarily select the first file while rebuilding the resource list.
        with QSignalBlocker(self.folder_combo), QSignalBlocker(self.image_combo):
            self.folder_combo.setCurrentText(str(path.parent))
            self._refresh_image_names(str(path.parent), select=False)
            self.image_combo.setCurrentText(path.name)
        # Preserve portable references while publishing the new image only once.
        self._apply_image_path(original)

    def _sync_selected_image(self):
        """The visible selection is authoritative at both test and save time."""
        name = self.image_combo.currentText()
        selected = str(Path(self.folder_combo.currentText()) / name) if name else ''
        stored = self.ui.parameter_0.text()
        resolved = self._resolved_image_path(stored)
        if not selected or not resolved or Path(selected).resolve() != Path(resolved).resolve():
            self._apply_image_path(selected)

    def _image_project_path(self):
        return (getattr(self.context, 'metadata', {}).get('project_path')
                or self.db.get_setting_value('当前文件路径'))

    def _resolved_image_path(self, path=None):
        value = str(path if path is not None else self.ui.parameter_0.text())
        return resolve_image_reference(value, project_path=self._image_project_path(),
                                       resource_folders=self.db.extract_resource_folder_path())

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
        open_advanced_timing = _module_imports.load('open_advanced_timing')
        open_advanced_timing(self, self.db)

    def _run_auxiliary(self, key):
        if key == '图像路径':
            path, _ = QFileDialog.getOpenFileName(self, '选择图片', self.folder_combo.currentText(), '图像 (*.png *.jpg *.jpeg *.bmp *.webp)')
            if path:
                self._set_image_path(path)
        elif key == '点击位置':
            try:
                dialog = ImagePositionDialog(self._resolved_image_path(), self.ui.parameter_6.text(), self)
                if dialog.exec() == QDialog.DialogCode.Accepted:
                    self.ui.parameter_6.setText(dialog.value())
            except ValueError as error:
                QMessageBox.warning(self, '点击位置', str(error))
        elif key == '区域':
            try:
                selected = pick_fixed_region(self)
                if selected is not None:
                    binding_parameters, _, _ = _module_imports.load('binding_parameters_select_background_save_capture')
                    binding = binding_parameters(self)
                    if binding is not None:
                        selected = region_in_bound_window(selected, binding)
                    self.ui.parameter_3.setText(str(selected))
                    self.region_group.setChecked(True)
                    self._refresh_region_mode()
            except Exception as error:
                QMessageBox.warning(self, '区域选择失败', str(error))
        else:
            super()._run_auxiliary(key)

    def _region_preview_tab_changed(self, *_):
        if self.tabs.currentWidget() is self.region_preview_page:
            self._capture_region_preview(fullscreen=False)

    def _capture_region_preview(self, fullscreen=True):
        if getattr(self, '_region_capture_pending', False):
            return
        self._region_capture_pending = True
        self.region_screenshot_button.setEnabled(False)
        self.follow_screenshot_button.setEnabled(False)
        visible = [(w, w.windowOpacity()) for w in QApplication.topLevelWidgets() if w.isVisible()]
        for widget, _ in visible:
            widget.setWindowOpacity(0)
        def capture():
            error = None
            try:
                from anclicker.ui.region_screenshot import capture_desktop
                pixmap, area = capture_desktop()
                self._region_screen_area = area
                binding_parameters, _, _ = _module_imports.load('binding_parameters_select_background_save_capture')
                binding = binding_parameters(self)
                if binding is not None and self.region_group.isChecked():
                    from anclicker.platform.background_runtime import Windows
                    windows = Windows()
                    target = windows.resolve(binding)
                    origin = windows.gui.ClientToScreen(int(target['窗口句柄']), (0,0))
                    area = (area[0]-origin[0],area[1]-origin[1],area[2],area[3])
                self._region_canvas_area = area
                self._update_region_preview()
                self.region_preview.set_background(pixmap, area)
                self.region_preview.set_region(area,
                    (self.region_preview.region.x(),self.region_preview.region.y(),self.region_preview.region.width(),self.region_preview.region.height()) if self.region_preview.region is not None else None,
                    '截图预览 · 拖动边框调整范围')
            except Exception as exc:
                error = str(exc)
            finally:
                for widget, opacity in visible:
                    try: widget.setWindowOpacity(opacity)
                    except RuntimeError: pass
                try:
                    self._region_capture_pending = False
                    self.region_screenshot_button.setEnabled(True)
                    self.follow_screenshot_button.setEnabled(True)
                except RuntimeError:
                    return
            if error:
                QMessageBox.warning(self, '截图预览失败', error)
            elif fullscreen and self.isVisible() and self.tabs.currentWidget() is self.region_preview_page:
                self.region_preview.open_fullscreen()
        QTimer.singleShot(180, capture)

    def _update_region_preview(self, *_):
        if not hasattr(self, 'region_preview') or self.tabs.currentWidget() is not self.region_preview_page:
            return
        self.region_offset_box.setVisible((getattr(self, 'WINDOW_IMAGE', False) or self.follow_region_group.isChecked()))
        self.region_screenshot_button.setVisible(not (getattr(self, 'WINDOW_IMAGE', False) or self.follow_region_group.isChecked()))
        try:
            if (getattr(self, 'WINDOW_IMAGE', False) or self.follow_region_group.isChecked()):
                if not self._region_target: raise ValueError('请先点选跟随窗口')
                target = dict(self._region_target)
                target.pop('区域比例', None)
                target.pop('区域偏移', None)
                for spin, value in zip(self.region_offset_spins,self._region_target.get('区域偏移',[0,0,0,0])):
                    with QSignalBlocker(spin): spin.setValue(int(value))
                self._preview_window_rect = window_region(target)
                screen = self.screen().virtualGeometry()
                area = getattr(self, '_region_screen_area', (screen.x(),screen.y(),screen.width(),screen.height()))
                region = window_region(self._region_target)
                x=min(area[0],region[0]); y=min(area[1],region[1])
                area=(x,y,max(area[0]+area[2],region[0]+region[2])-x,max(area[1]+area[3],region[1]+region[3])-y)
            elif self.region_group.isChecked():
                region = actions.region(self.ui.parameter_3.text())
                screen = self.screen().virtualGeometry()
                area = getattr(self, '_region_canvas_area', (screen.x(), screen.y(), screen.width(), screen.height()))
                if region:
                    x=min(area[0],region[0]); y=min(area[1],region[1])
                    area=(x,y,max(area[0]+area[2],region[0]+region[2])-x,max(area[1]+area[3],region[1]+region[3])-y)
            else:
                self.region_preview.set_region((0,0,1920,1080), None, '请选择并启用区域识别')
                return
            self.region_preview.set_region(area, region, '拖动边框或角点调整范围' if region else '请先设置区域')
        except Exception as error:
            self.region_preview.set_region((0,0,1920,1080), None, str(error))

    def _preview_region_changed(self, region):
        if (getattr(self, 'WINDOW_IMAGE', False) or self.follow_region_group.isChecked()) and self._region_target:
            x,y,w,h=self._preview_window_rect
            rx,ry,rw,rh=region
            self._region_target.pop('区域比例', None)
            offsets=[rx-x,ry-y,rx+rw-x-w,ry+rh-y-h]
            self._region_target['区域偏移']=offsets
            for spin, value in zip(self.region_offset_spins,offsets):
                with QSignalBlocker(spin): spin.setValue(value)
        else:
            with QSignalBlocker(self.ui.parameter_3):
                self.ui.parameter_3.setText(str(region))

    def _region_offsets_changed(self, *_):
        if not (getattr(self, 'WINDOW_IMAGE', False) or self.follow_region_group.isChecked()) or not self._region_target:
            return
        self._region_target.pop('区域比例', None)
        self._region_target['区域偏移']=[spin.value() for spin in self.region_offset_spins]
        self._update_region_preview()

    def _toggle_region_group(self, following, checked):
        if checked:
            other = self.region_group if following else self.follow_region_group
            other.setChecked(False)
        self._update_region_preview()

    def _refresh_region_mode(self):
        following = self._region_target is not None
        self.ui.parameter_3.setReadOnly(False)
        title = (self._region_target or {}).get('窗口标题', '')
        self.region_hint.setText('跟随窗口：' + title if following else '未选择跟随窗口')
        self.region_hint.setToolTip(self.region_hint.text())
        self._update_region_preview()

    def _pick_follow_region(self):
        try:
            target = pick_background_window(self)
            if target is None:
                return
            selected = window_region(target)
            self._region_target = dict(target)
            self._follow_region = str(selected)
            self.follow_region_group.setChecked(True)
            self._refresh_region_mode()
        except Exception as error:
            QMessageBox.warning(self, '窗口区域选择失败', str(error))

    def _select_screen(self, capture):
        BINDING = _module_imports.load('BINDING')
        if BINDING == 'PySide2':
            isValid = _module_imports.load('isValid')
        else:
            isValid = _module_imports.load('isValid_2')
        if getattr(self, '_screen_selection_active', False):
            return
        if capture:
            Path(IMAGES_FOLDER).mkdir(parents=True, exist_ok=True)
        binding_parameters, select_background, save_capture = _module_imports.load('binding_parameters_select_background_save_capture')
        try:
            parameters = binding_parameters(self)
            if parameters is not None:
                selection = select_background(self, parameters)
                if selection is not None:
                    if capture:
                        path = save_capture(self, selection)
                        self._set_image_path(path)
                    else:
                        self.ui.parameter_3.setText(str(selection.region))
                        self.region_group.setChecked(True)
                return
        except Exception as error:
            if isValid(self):
                QMessageBox.warning(self, '后台截图/区域设置失败', str(error))
            return
        host = self.parentWidget().window() if self.parentWidget() else None
        host_visible = host is not None and host.isVisible()
        was_visible = self.isVisible()
        opacity = self.windowOpacity()
        host_opacity = host.windowOpacity() if host_visible else None
        buttons_enabled = self.ui.buttonBox.isEnabled()
        self._screen_selection_active = True
        self.ui.buttonBox.setEnabled(False)
        # Hiding a modal editor ends exec(); opacity keeps its event loop alive.
        self.setWindowOpacity(0.0)
        if host_visible:
            host.setWindowOpacity(0.0)
        def restore():
            if host_visible and isValid(host):
                host.setWindowOpacity(host_opacity)
            if not isValid(self):
                return
            self._screen_selection_active = False
            self.ui.buttonBox.setEnabled(buttons_enabled)
            self.setWindowOpacity(opacity)
            # A cancelled or closed editor must not be reopened by a late callback.
            if not was_visible or self.isVisible():
                self.show(); self.raise_(); self.activateWindow()
        def choose():
            selector = None
            try:
                if not isValid(self) or (was_visible and not self.isVisible()):
                    return
                selector = SmartCaptureDialog() if capture else _RegionSelectionDialog()
                selector.exec()
                if not isValid(self) or (was_visible and not self.isVisible()):
                    return
                region = selector.selected_region()
                # Selection already contains the captured pixels. Commit immediately
                # so confirmation cannot overtake a second arbitrary delay.
                if region and capture:
                    path = Path(IMAGES_FOLDER) / f'截图_{datetime.now():%Y%m%d_%H%M%S_%f}.png'
                    path.parent.mkdir(parents=True, exist_ok=True)
                    selector.save_selection(path)
                    self._set_image_path(path)
                    callback = getattr(self.context, 'metadata', {}).get('remember_capture')
                    if callable(callback):
                        callback(str(path))
                elif region:
                    self.ui.parameter_3.setText(str(region))
                    self.region_group.setChecked(True)
            except Exception as error:
                if isValid(self):
                    restore()
                    QMessageBox.warning(self, '截图/区域设置失败', str(error))
            finally:
                if selector is not None and (not isinstance(selector, QDialog) or isValid(selector)):
                    selector.deleteLater()
                restore()
        QTimer.singleShot(180, choose)

    def load_draft(self, draft):
        draft = draft if isinstance(draft, InstructionDraft) else InstructionDraft.from_mapping(draft)
        super().load_draft(draft)
        if not hasattr(self, 'folder_combo'):
            return
        path = self.ui.parameter_0.text()
        if path:
            self._set_image_path(path)
        self._region_target = dict(draft.parameters.get('区域窗口') or {}) if draft.parameters.get('区域模式') == '跟随窗口' else None
        self._refresh_region_mode()
        region = self.ui.parameter_3.text()
        self._follow_region = region
        following = self._region_target is not None
        self.region_group.setChecked(not following and region.replace(' ', '') not in ('', '(0,0,0,0)', '0,0,0,0'))
        self.follow_region_group.setChecked(following)
        policy = self.ui.parameter_2.text()
        if policy not in ('自动略过', '自动跳过', ''):
            try:
                self.timeout_spin.setValue(int(float(policy)))
            except ValueError:
                pass
            self.skip_check.setChecked(False)
        else:
            self.skip_check.setChecked(True)
            if self.ui.parameter_1.currentText() == '无操作':
                self.timeout_spin.setValue(1)
        self._image_action_changed()
        self._configure_region_columns()

    def get_draft(self):
        self._sync_selected_image()
        # Disabled region retains its coordinates for toggling back, but is not executed.
        control = self.ui.parameter_3
        saved = control.text()
        following = (getattr(self, 'WINDOW_IMAGE', False) or self.follow_region_group.isChecked())
        enabled = following or self.region_group.isChecked()
        if following:
            control.setText(getattr(self, '_follow_region', '') or saved)
        elif not enabled:
            control.setText('')
        try:
            draft = super().get_draft()
            if self.region_group.isChecked() and actions.region(saved) is None:
                raise ValueError('请先设置有效识别区域。')
            if following:
                if not self._region_target:
                    raise ValueError('请重新点选跟随窗口。')
                offsets = self._region_target.get('区域偏移',[0,0,0,0])
                base = actions.region(getattr(self, '_follow_region', '') or saved)
                if base and (base[2]+offsets[2]-offsets[0]<=0 or base[3]+offsets[3]-offsets[1]<=0):
                    raise ValueError('偏移后的区域宽度和高度必须大于 0')
                draft.parameters['区域模式'] = '跟随窗口'
                draft.parameters['区域窗口'] = dict(self._region_target)
            return draft
        finally:
            control.setText(saved)

    def _valid_image(self):
        self._sync_selected_image()
        path = self._resolved_image_path()
        if path and not Path(path).is_file():
            from anclicker.app.paths import PORTABLE_DATA_FOLDER
            folder = QFileDialog.getExistingDirectory(self, '未找到图片，请选择图片所在文件夹', PORTABLE_DATA_FOLDER)
            if not folder:
                return False
            name = Path(path).name
            matches = sorted(p for p in Path(folder).rglob(name) if p.is_file())
            if len(matches) != 1:
                QMessageBox.warning(self, '未找到唯一图片', '所选文件夹中未找到图片或存在同名图片，请使用“选择图片”指定文件。')
                return False
            self.db.writes_to_resource_folder_path(folder)
            self._set_image_path(str(matches[0]))
            path = self._resolved_image_path()
        pixmap = QPixmap()
        if path:
            try:
                pixmap.loadFromData(Path(path).read_bytes())
            except OSError:
                pass
        if pixmap.isNull():
            QMessageBox.warning(self, '图像文件无效', '图像文件不存在或无法读取，请重新选择图片。')
            return False
        return True

    def _accept_if_valid(self):
        if self._valid_image():
            super()._accept_if_valid()

    def _test_if_valid(self):
        if self._valid_image():
            super()._test_if_valid()
