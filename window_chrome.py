"""Compact title bar with a theme control beside the window controls."""
import math
from PySide6.QtCore import QEvent, QLineF, QRectF, Qt
from PySide6.QtGui import QColor, QIcon, QPainter, QPainterPath, QPen, QPixmap
from PySide6.QtWidgets import QApplication, QFrame, QHBoxLayout, QLabel, QSizePolicy, QToolButton, QVBoxLayout, QWidget


def chrome_icon(kind, color):
    pixmap = QPixmap(40, 40)
    pixmap.setDevicePixelRatio(2)
    pixmap.fill(Qt.GlobalColor.transparent)
    painter = QPainter(pixmap)
    painter.setRenderHint(QPainter.RenderHint.Antialiasing)
    painter.setPen(QPen(QColor(color), 1.5))
    if kind == "sun":
        painter.drawEllipse(QRectF(6, 6, 8, 8))
        for index in range(8):
            angle = index * math.pi / 4
            painter.drawLine(QLineF(10 + 6 * math.cos(angle), 10 + 6 * math.sin(angle),
                                    10 + 8 * math.cos(angle), 10 + 8 * math.sin(angle)))
    elif kind == "moon":
        outer, cutout = QPainterPath(), QPainterPath()
        outer.addEllipse(QRectF(3, 3, 14, 14))
        cutout.addEllipse(QRectF(8, 0, 13, 13))
        painter.drawPath(outer.subtracted(cutout))
    elif kind == "minimize":
        painter.drawLine(5, 10, 15, 10)
    elif kind == "maximize":
        painter.drawRoundedRect(QRectF(5, 5, 10, 10), 1, 1)
    elif kind == "restore":
        painter.drawLine(7, 4, 16, 4)
        painter.drawLine(16, 4, 16, 13)
        painter.drawLine(7, 4, 7, 6)
        painter.drawLine(14, 13, 16, 13)
        painter.drawRect(QRectF(4, 7, 9, 9))
    else:
        painter.drawLine(6, 6, 14, 14)
        painter.drawLine(14, 6, 6, 14)
    painter.end()
    return QIcon(pixmap)


class WindowTitleBar(QFrame):
    def __init__(self, window, theme_action):
        super().__init__(window)
        self.host = window
        self.setObjectName("windowTitleBar")
        self.setFixedHeight(44)
        self._drag_offset = None
        self._resize_origin = None
        self._resize_edges = Qt.Edge(0)
        self._color = "#eeeeef"
        layout = QHBoxLayout(self)
        layout.setContentsMargins(12, 5, 10, 5)
        layout.setSpacing(6)
        logo = QLabel()
        logo.setPixmap(window.windowIcon().pixmap(22, 22))
        logo.setAttribute(Qt.WidgetAttribute.WA_TransparentForMouseEvents)
        layout.addWidget(logo)
        self.title = QLabel(window.windowTitle())
        self.title.setObjectName("windowCaption")
        self.title.setSizePolicy(QSizePolicy.Policy.Ignored, QSizePolicy.Policy.Preferred)
        self.title.setAttribute(Qt.WidgetAttribute.WA_TransparentForMouseEvents)
        window.windowTitleChanged.connect(self.title.setText)
        layout.addWidget(self.title, 1)
        self.theme_button = self._button("themeToggle", "切换主题")
        self.theme_button.setDefaultAction(theme_action)
        self.theme_button.setToolButtonStyle(Qt.ToolButtonStyle.ToolButtonIconOnly)
        self.minimize_button = self._button("windowMinimize", "最小化")
        self.minimize_button.clicked.connect(window.showMinimized)
        self.maximize_button = self._button("windowMaximize", "最大化")
        self.maximize_button.clicked.connect(self.toggle_maximized)
        self.close_button = self._button("windowClose", "关闭")
        self.close_button.clicked.connect(window.close)
        for button in (self.theme_button, self.minimize_button, self.maximize_button, self.close_button):
            layout.addWidget(button)
        QApplication.instance().installEventFilter(self)

    def _button(self, name, label):
        button = QToolButton(self)
        button.setObjectName(name)
        button.setAccessibleName(label)
        button.setToolTip(label)
        button.setFixedSize(32, 32)
        return button

    def apply_theme(self, mode, colors):
        self._color = colors['text']
        label = "切换浅色主题" if mode == "dark" else "切换深色主题"
        self.theme_button.defaultAction().setIcon(chrome_icon("sun" if mode == "dark" else "moon", self._color))
        self.theme_button.setAccessibleName(label)
        self.theme_button.setToolTip(label)
        self.minimize_button.setIcon(chrome_icon("minimize", self._color))
        self.close_button.setIcon(chrome_icon("close", "#ffffff"))
        self._update_maximize()
        self.setStyleSheet(f"""
            QFrame#windowTitleBar {{ background: {colors['surface']}; border-bottom: 1px solid {colors['line']}; }}
            QLabel#windowCaption {{ color: {colors['text']}; font-weight: 600; background: transparent; }}
            QToolButton {{ background: transparent; border: none; border-radius: 16px; padding: 0; }}
            QToolButton:hover, QToolButton:focus {{ background: {colors['surface3']}; }}
            QToolButton#windowClose {{ background: #dc3545; }}
            QToolButton#windowClose:hover {{ background: #ef4657; }}
        """)

    def _update_maximize(self):
        maximized = self.host.isMaximized()
        self.maximize_button.setIcon(chrome_icon("restore" if maximized else "maximize", self._color))
        label = "还原窗口" if maximized else "最大化"
        self.maximize_button.setToolTip(label)
        self.maximize_button.setAccessibleName(label)

    def toggle_maximized(self):
        self.host.showNormal() if self.host.isMaximized() else self.host.showMaximized()
        self._update_maximize()

    def mouseDoubleClickEvent(self, event):
        if event.button() == Qt.MouseButton.LeftButton:
            self.toggle_maximized()
            event.accept()

    def mousePressEvent(self, event):
        if event.button() == Qt.MouseButton.LeftButton:
            handle = self.host.windowHandle()
            if handle and handle.startSystemMove():
                event.accept()
                return
            if not self.host.isMaximized():
                self._drag_offset = event.globalPosition().toPoint() - self.host.pos()

    def mouseMoveEvent(self, event):
        if self._drag_offset is not None and event.buttons() & Qt.MouseButton.LeftButton:
            self.host.move(event.globalPosition().toPoint() - self._drag_offset)

    def mouseReleaseEvent(self, event):
        self._drag_offset = None

    def edges_at(self, position):
        edges = Qt.Edge(0)
        if self.host.isMaximized() or self.host.isFullScreen():
            return edges
        if position.x() < 5:
            edges |= Qt.Edge.LeftEdge
        elif position.x() >= self.host.width() - 5:
            edges |= Qt.Edge.RightEdge
        if position.y() < 5:
            edges |= Qt.Edge.TopEdge
        elif position.y() >= self.host.height() - 5:
            edges |= Qt.Edge.BottomEdge
        return edges

    def eventFilter(self, watched, event):
        # During Qt teardown many unrelated QObject events pass this global
        # filter; never dereference widget/window wrappers for those events.
        kind = event.type()
        if kind not in (QEvent.Type.WindowStateChange, QEvent.Type.MouseButtonPress,
                        QEvent.Type.MouseMove, QEvent.Type.MouseButtonRelease):
            return False
        from shiboken6 import isValid
        if not isValid(self.host) or not isValid(watched):
            return False
        if watched is self.host and event.type() == QEvent.Type.WindowStateChange:
            self._update_maximize()
        if not isinstance(watched, QWidget) or watched.window() is not self.host:
            return False
        if event.type() == QEvent.Type.MouseButtonPress and event.button() == Qt.MouseButton.LeftButton:
            edges = self.edges_at(self.host.mapFromGlobal(event.globalPosition().toPoint()))
            if edges:
                handle = self.host.windowHandle()
                if handle and handle.startSystemResize(edges):
                    return True
                self._resize_edges = edges
                self._resize_origin = (event.globalPosition().toPoint(), self.host.geometry())
                return True
        elif event.type() == QEvent.Type.MouseMove and self._resize_origin is not None:
            start, rect = self._resize_origin
            delta = event.globalPosition().toPoint() - start
            updated = type(rect)(rect)
            if self._resize_edges & Qt.Edge.LeftEdge:
                updated.setLeft(min(rect.left() + delta.x(), rect.right() - self.host.minimumWidth() + 1))
            if self._resize_edges & Qt.Edge.RightEdge:
                updated.setRight(max(rect.right() + delta.x(), rect.left() + self.host.minimumWidth() - 1))
            if self._resize_edges & Qt.Edge.TopEdge:
                updated.setTop(min(rect.top() + delta.y(), rect.bottom() - self.host.minimumHeight() + 1))
            if self._resize_edges & Qt.Edge.BottomEdge:
                updated.setBottom(max(rect.bottom() + delta.y(), rect.top() + self.host.minimumHeight() - 1))
            self.host.setGeometry(updated)
            return True
        elif event.type() == QEvent.Type.MouseButtonRelease:
            self._resize_origin = None
        return False


def install_title_bar(window, theme_action):
    window.setWindowFlag(Qt.WindowType.FramelessWindowHint, True)
    menu = window.menuBar()
    # Reparent before replacing QMainWindow's menu widget to preserve all menus.
    menu.setParent(None)
    host = QWidget(window)
    host.setObjectName("windowHeader")
    layout = QVBoxLayout(host)
    layout.setContentsMargins(0, 0, 0, 0)
    layout.setSpacing(0)
    bar = WindowTitleBar(window, theme_action)
    layout.addWidget(bar)
    layout.addWidget(menu)
    window.setMenuWidget(host)
    return bar
