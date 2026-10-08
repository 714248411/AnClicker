"""Main-window chrome backed by PySideSix-Frameless-Window."""
import math
from PySide6.QtCore import QLineF, QRect, QRectF, QSize, Qt
from PySide6.QtGui import QColor, QIcon, QPainter, QPainterPath, QPen, QPixmap
from PySide6.QtWidgets import QAbstractButton, QHBoxLayout, QLabel, QPushButton, QSizePolicy, QToolButton, QWidget
from info import APP_NAME, CURRENT_VERSION
from qframelesswindow import FramelessMainWindow, StandardTitleBar
from qframelesswindow.titlebar import TitleBarButton
from qframelesswindow.utils import toggleMaxState


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
    elif kind == "update":
        painter.drawEllipse(QRectF(2, 2, 16, 16))
        painter.drawLine(10, 14, 10, 6)
        painter.drawLine(10, 6, 6, 10)
        painter.drawLine(10, 6, 14, 10)
    elif kind == "minimize":
        painter.drawLine(5, 10, 15, 10)
    elif kind == "maximize":
        painter.drawRoundedRect(QRectF(5, 5, 10, 10), 1, 1)
    elif kind == "compact":
        painter.drawRoundedRect(QRectF(3, 4, 14, 12), 2, 2)
        painter.drawLine(10, 4, 10, 16)
        painter.drawLine(12, 8, 15, 8)
        painter.drawLine(12, 11, 15, 11)
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


class ChromeControlButton(TitleBarButton):
    """Use a centered square icon instead of the library's fixed 46x32 artwork."""
    def __init__(self, kind, parent):
        super().__init__(parent)
        self.kind = kind

    def setMaxState(self, maximized):
        self.kind = 'restore' if maximized else 'maximize'
        self.update()

    def paintEvent(self, event):
        color, background = self._getColors()
        painter = QPainter(self)
        painter.setRenderHint(QPainter.RenderHint.Antialiasing)
        painter.setPen(Qt.PenStyle.NoPen)
        painter.setBrush(background)
        painter.drawRoundedRect(QRectF(self.rect()), 6, 6)
        chrome_icon(self.kind, color).paint(painter, QRect((self.width()-18)//2, (self.height()-18)//2, 18, 18))


class UpdateNoticeButton(QPushButton):
    def __init__(self, parent):
        super().__init__('新版本', parent)
        self.setObjectName('updateNotice')
        self.setCursor(Qt.CursorShape.PointingHandCursor)
        self.setFixedHeight(32)
        self.setIconSize(QSize(18, 18))
        self.badge = QWidget(self)
        self.badge.setFixedSize(8, 8)
        self.badge.setStyleSheet('background: #ef4444; border-radius: 4px;')
        self.badge.setAttribute(Qt.WidgetAttribute.WA_TransparentForMouseEvents)
        self.hide()

    def resizeEvent(self, event):
        super().resizeEvent(event)
        self.badge.move(self.width() - 9, 1)
        self.badge.raise_()


class WindowTitleBar(StandardTitleBar):
    def __init__(self, window, theme_action):
        super().__init__(window)
        self.setFixedHeight(48)
        self.setObjectName('windowTitleBar')
        # Keep the library's native window behavior; replace only button artwork.
        for name, kind in (('minBtn', 'minimize'), ('maxBtn', 'maximize'), ('closeBtn', 'close')):
            old = getattr(self, name)
            index = self.hBoxLayout.indexOf(old)
            self.hBoxLayout.removeWidget(old)
            old.hide()
            old.deleteLater()
            button = ChromeControlButton(kind, self)
            self.hBoxLayout.insertWidget(index, button, 0, Qt.AlignmentFlag.AlignVCenter)
            setattr(self, name, button)
        self.minBtn.clicked.connect(window.showMinimized)
        self.maxBtn.clicked.connect(lambda: toggleMaxState(window))
        self.closeBtn.clicked.connect(window.close)
        self.hBoxLayout.setContentsMargins(0, 0, 8, 0)
        self.hBoxLayout.setSpacing(4)
        self._ready_version = ''
        self._ready_notes = ''
        self.titleLabel.setMinimumWidth(0)
        self.titleLabel.setSizePolicy(QSizePolicy.Policy.Preferred, QSizePolicy.Policy.Preferred)
        title_index = self.hBoxLayout.indexOf(self.titleLabel)
        self.hBoxLayout.removeWidget(self.titleLabel)
        identity = QWidget(self)
        identity_layout = QHBoxLayout(identity)
        identity_layout.setContentsMargins(0, 0, 0, 0)
        identity_layout.setSpacing(8)
        identity_layout.addWidget(self.titleLabel)
        self.versionLabel = QLabel(CURRENT_VERSION, identity)
        identity_layout.addWidget(self.versionLabel)
        self.hBoxLayout.insertWidget(title_index, identity)
        for label in (self.titleLabel, self.versionLabel):
            label.setAttribute(Qt.WidgetAttribute.WA_TransparentForMouseEvents)
        self.setTitle(window.windowTitle())
        self.setIcon(window.windowIcon())
        self.updateButton = UpdateNoticeButton(self)
        self.hBoxLayout.insertWidget(self.hBoxLayout.indexOf(self.minBtn), self.updateButton)
        self.compact_button = QToolButton(self)
        self.compact_button.setCheckable(True)
        self.compact_button.setToolTip('小化：仅显示控制与操作')
        self.theme_button = QToolButton(self)
        self.theme_button.setDefaultAction(theme_action)
        self.theme_button.setToolButtonStyle(Qt.ToolButtonStyle.ToolButtonIconOnly)
        for button in (self.compact_button, self.theme_button):
            button.setFixedSize(32, 32)
            button.setIconSize(QSize(18, 18))
            self.hBoxLayout.insertWidget(self.hBoxLayout.indexOf(self.minBtn), button)
        for button, label in ((self.minBtn, '最小化'), (self.maxBtn, '最大化/还原'), (self.closeBtn, '关闭')):
            button.setFixedSize(32, 32)
            button.setToolTip(label)
            button.setAccessibleName(label)

    def setTitle(self, title):
        # Keep the OS window title unchanged; render identity and version separately.
        self.titleLabel.setText(APP_NAME)

    def canDrag(self, pos):
        child = self.childAt(pos)
        while child is not None and child is not self:
            if isinstance(child, QAbstractButton):
                return False
            child = child.parentWidget()
        return super().canDrag(pos)

    def show_update(self, version, notes=''):
        self._ready_version, self._ready_notes = str(version), str(notes)
        self.updateButton.setToolTip(f'新版本 {version} 已准备完成，点击保存项目并重启更新。\n\n{notes}')
        self.set_update_applying(False)
        self.updateButton.show()

    def set_update_applying(self, applying):
        self.updateButton.setText('正在更新…' if applying else '新版本')
        self.updateButton.setEnabled(not applying)
        self.updateButton.badge.setVisible(not applying)

    def apply_theme(self, mode, colors):
        color = QColor(colors['text'])
        self.titleLabel.setStyleSheet(f"color: {colors['text']}; background: transparent; padding: 0; font-family: 'Microsoft YaHei UI'; font-size: 16px; font-weight: 700;")
        version_color = '#94a3b8' if mode == 'dark' else '#475569'
        self.versionLabel.setStyleSheet(f"color: {version_color}; background: transparent; padding: 0; font-family: 'Microsoft YaHei UI'; font-size: 13px; font-weight: 400;")
        self.setStyleSheet(f"""
            WindowTitleBar {{ background: {colors['surface']}; }}
            QToolButton, QPushButton#updateNotice {{ color: {colors['text']}; background: transparent;
                border: none; border-radius: 6px; padding: 0; }}
            QPushButton#updateNotice {{ padding: 0 10px; }}
            QToolButton:hover, QPushButton#updateNotice:hover {{ background: {colors['surface3']}; }}
            QToolButton:pressed, QToolButton:checked, QPushButton#updateNotice:pressed {{ background: {colors['line']}; }}
        """)
        for button in (self.minBtn, self.maxBtn, self.closeBtn):
            button.setNormalColor(color)
            button.setHoverColor(color)
            button.setPressedColor(color)
            button.setHoverBackgroundColor(QColor(colors['surface3']))
            button.setPressedBackgroundColor(QColor(colors['line']))
        self.closeBtn.setHoverColor(QColor('white'))
        self.closeBtn.setPressedColor(QColor('white'))
        self.closeBtn.setHoverBackgroundColor(QColor('#dc3545'))
        self.closeBtn.setPressedBackgroundColor(QColor('#b42332'))
        self.compact_button.setIcon(chrome_icon('compact', colors['text']))
        self.theme_button.defaultAction().setIcon(chrome_icon('sun' if mode == 'dark' else 'moon', colors['text']))
        self.theme_button.setToolTip('切换浅色主题' if mode == 'dark' else '切换深色主题')
        self.updateButton.setIcon(chrome_icon('update', colors['text']))


def install_title_bar(window, theme_action):
    bar = WindowTitleBar(window, theme_action)
    window.setTitleBar(bar)
    # Reserve space for the floating library title bar above the entire main layout.
    window.setContentsMargins(0, bar.height(), 0, 0)
    bar.resize(window.width(), bar.height())
    bar.show()
    bar.raise_()
    return bar


def validate_window_chrome(window):
    """Require usable title controls, not merely a visible top-level window."""
    bar = window.view_workspace.title_bar
    controls = (bar.minBtn, bar.maxBtn, bar.closeBtn)
    visible = (bar is window.titleBar and bar.isVisibleTo(window)
               and all(button.isVisibleTo(window) and button.isEnabled()
                       and bar.rect().contains(button.geometry()) for button in controls))
    menu_below = window.menubar.mapTo(window, window.menubar.rect().topLeft()).y() >= bar.height()
    if not visible or not menu_below:
        raise RuntimeError('标题栏、窗口按钮或菜单布局验收失败')
    return True
