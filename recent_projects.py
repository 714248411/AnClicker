"""Recent project picker and window-scoped external workbook drops."""
import os
from pathlib import PureWindowsPath, PurePosixPath

from qt_compat.QtCore import QObject, QEvent, Qt, Signal, QTimer
from qt_compat.QtWidgets import QComboBox, QWidget, QVBoxLayout, QLabel, QApplication


def short_path(path):
    parsed = PureWindowsPath(path) if '\\' in path or ':' in path else PurePosixPath(path)
    parts = parsed.parts
    return ('…/' if len(parts) > 3 else '') + '/'.join(parts[-3:])


def dropped_project(mime):
    if not mime.hasUrls():
        return None
    urls = mime.urls()
    if len(urls) != 1 or not urls[0].isLocalFile():
        return None
    path = os.path.normpath(urls[0].toLocalFile())
    return path if os.path.splitext(path)[1].lower() == '.xlsx' and os.path.isfile(path) else None


class RecentProjectPicker(QWidget):
    openRequested = Signal(str)

    def __init__(self, parent=None):
        super().__init__(parent)
        self.current_path = ''
        layout = QVBoxLayout(self)
        layout.setContentsMargins(0, 0, 0, 0)
        layout.setSpacing(3)
        label = QLabel('最近项目 · 可编辑路径 / 拖入文件', self)
        label.setWordWrap(True)
        layout.addWidget(label)
        self.combo = QComboBox(self)
        self.combo.setEditable(True)
        self.combo.setInsertPolicy(QComboBox.NoInsert)
        self.combo.setCompleter(None)
        self.combo.setMinimumWidth(0)
        self.combo.setMinimumContentsLength(8)
        self.combo.setSizeAdjustPolicy(QComboBox.AdjustToMinimumContentsLengthWithIcon)
        self.combo.lineEdit().setPlaceholderText('输入完整 .xlsx 路径后按回车')
        self.combo.lineEdit().installEventFilter(self)
        self.combo.activated.connect(self._activated)
        self.combo.lineEdit().returnPressed.connect(self._typed)
        layout.addWidget(self.combo)

    def refresh(self, paths, current):
        self.current_path = current if current and current != 'None' else ''
        self.combo.blockSignals(True)
        self.combo.clear()
        unique = list(dict.fromkeys(([self.current_path] if self.current_path else []) + list(paths)))
        for path in unique:
            self.combo.addItem(short_path(path), path)
            self.combo.setItemData(self.combo.count()-1, path, Qt.ToolTipRole)
        self.combo.setCurrentIndex(0 if self.current_path else -1)
        self.combo.setEditText(self.current_path if self.combo.lineEdit().hasFocus() else short_path(self.current_path))
        self.combo.setToolTip(self.current_path)
        self.combo.blockSignals(False)

    def _activated(self, index):
        path = self.combo.itemData(index)
        if path:
            self.combo.setEditText(path)
            self.openRequested.emit(path)

    def _typed(self):
        text = self.combo.currentText().strip().strip('"')
        # Enter can be emitted by an open popup: never interpret its abbreviated
        # label as a filesystem path or open the same project twice.
        if text == short_path(self.current_path):
            return
        if text:
            self.openRequested.emit(os.path.abspath(os.path.expanduser(os.path.expandvars(text))))

    def eventFilter(self, watched, event):
        if event.type() == QEvent.FocusIn and self.combo.currentText() == short_path(self.current_path):
            self.combo.setEditText(self.current_path)
        elif event.type() == QEvent.FocusOut and self.combo.currentText() == self.current_path:
            QTimer.singleShot(0, lambda: self.combo.setEditText(short_path(self.current_path))
                              if not self.combo.lineEdit().hasFocus() else None)
        return False


class ProjectDropFilter(QObject):
    """Intercept only external .xlsx files; preserve internal instruction drags."""
    def __init__(self, window, callback):
        super().__init__(window)
        self.window, self.callback = window, callback
        for widget in [window] + window.findChildren(QWidget):
            widget.setAcceptDrops(True)
        QApplication.instance().installEventFilter(self)

    def eventFilter(self, watched, event):
        if event.type() not in (QEvent.DragEnter, QEvent.DragMove, QEvent.Drop):
            return False
        if not isinstance(watched, QWidget) or watched.window() is not self.window:
            return False
        if not event.mimeData().hasUrls():
            return False
        path = dropped_project(event.mimeData())
        if path:
            event.acceptProposedAction()
            if event.type() == QEvent.Drop:
                QTimer.singleShot(0, lambda: self.callback(path))
        else:
            event.ignore()
            self.window.statusBar.showMessage('请每次拖入一个 Clicker / An Clicker .xlsx 项目文件。', 5000)
        return True
