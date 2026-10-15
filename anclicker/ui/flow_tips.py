"""Compact tips checked against the node editor's implemented gestures and ports."""
from anclicker.platform.qt_compat.QtCore import Qt, QEvent, QTimer, Signal
from anclicker.platform.qt_compat.QtWidgets import QWidget, QLabel, QHBoxLayout, QToolButton, QMenu, QSizePolicy

from anclicker._imports import DeferredImports as _DeferredImports

# Dependencies declared here retain their existing on-demand loading boundaries.
_module_imports = _DeferredImports(globals(), {
    'style_context_menu': ('from', 'anclicker.ui.context_menu_style', ('style_context_menu',), 0),
})


SETTING = '显示流程图操作提示'
TIPS = (
    '条件分支：右侧圆点是“是”，顶部圆点是“否”。',
    '从输出圆点拖到目标节点左侧的输入圆点，即可连线。',
    '双击指令节点可配置参数；右键可备注、复制或运行。',
    '滚轮缩放画布；Ctrl + 左键拖动空白处可平移。',
    '复制多条指令后，按住 Ctrl + 左键拖动其中任意一个节点，可平移本次复制的整组指令。',
    '从空白处按住右键拖拽，划过连线后松开即可删除；Esc 可取消。',
    '右下橙色圆点是异常输出，可连接报错模块。',
    '选中节点后右击“存为模板”，下次可从空白处右键插入。',
    '点击“适应视图”，可查看整个流程。',
)


class TipLabel(QLabel):
    def __init__(self, parent=None):
        super().__init__(parent)
        self.full_text = ''
        self.setMinimumWidth(0)
        self.setSizePolicy(QSizePolicy.Ignored, QSizePolicy.Preferred)

    def set_tip(self, text):
        self.full_text = text
        self.setToolTip(text + '\n右键可收起提示')
        self.setAccessibleName(text)
        self.refresh_text()

    def refresh_text(self):
        self.setText(self.fontMetrics().elidedText(self.full_text, Qt.ElideRight, self.contentsRect().width()))

    def resizeEvent(self, event):
        super().resizeEvent(event)
        self.refresh_text()

    def changeEvent(self, event):
        super().changeEvent(event)
        if event.type() == QEvent.FontChange and hasattr(self, 'full_text'):
            self.refresh_text()


class FlowTips(QWidget):
    expandedChanged = Signal(bool)
    INTERVAL_MS = 6000

    def __init__(self, window, parent=None):
        super().__init__(parent)
        self.window = window
        self.index = 0
        self.hovered = False
        self.menu_open = False
        self.expanded = window.db.get_setting_value(SETTING) != 'False'
        self.setObjectName('flowTips')
        self.setAttribute(Qt.WA_StyledBackground, True)
        self.setAccessibleName('流程图操作提示')
        self.setSizePolicy(QSizePolicy.Expanding, QSizePolicy.Fixed)
        row = QHBoxLayout(self)
        row.setContentsMargins(10, 3, 6, 3)
        row.setSpacing(6)
        badge = QLabel('提示', self)
        badge.setObjectName('flowTipBadge')
        row.addWidget(badge)
        self.label = TipLabel(self)
        self.label.setObjectName('flowTipText')
        row.addWidget(self.label, 1)
        self.previous = QToolButton(self)
        self.previous.setText('‹')
        self.previous.setAccessibleName('上一条提示')
        self.previous.setToolTip('上一条提示')
        self.previous.clicked.connect(lambda: self.advance(-1))
        self.counter = QLabel(self)
        self.counter.setObjectName('flowTipCounter')
        self.counter.setAlignment(Qt.AlignCenter)
        self.next = QToolButton(self)
        self.next.setText('›')
        self.next.setAccessibleName('下一条提示')
        self.next.setToolTip('下一条提示')
        self.next.clicked.connect(lambda: self.advance(1))
        for button in (self.previous, self.next):
            button.setFixedSize(22, 22)
            button.installEventFilter(self)
        row.addWidget(self.previous)
        row.addWidget(self.counter)
        row.addWidget(self.next)
        self.timer = QTimer(self)
        self.timer.setInterval(self.INTERVAL_MS)
        self.timer.timeout.connect(self.advance)
        self.update_tip()
        self.setVisible(self.expanded)

    def update_tip(self):
        self.label.set_tip(TIPS[self.index])
        self.counter.setText(f'{self.index + 1}/{len(TIPS)}')

    def advance(self, direction=1):
        self.index = (self.index + direction) % len(TIPS)
        self.update_tip()
        self.sync_timer()

    def sync_timer(self):
        focused = self.previous.hasFocus() or self.next.hasFocus()
        if self.expanded and self.isVisible() and not (self.hovered or self.menu_open or focused):
            self.timer.start()
        else:
            self.timer.stop()

    def set_expanded(self, expanded):
        self.expanded = bool(expanded)
        self.window.db.set_setting_value(SETTING, str(self.expanded))
        self.setVisible(self.expanded)
        self.sync_timer()
        self.expandedChanged.emit(self.expanded)

    def showEvent(self, event):
        super().showEvent(event)
        self.hovered = self.underMouse()
        self.sync_timer()

    def hideEvent(self, event):
        self.timer.stop()
        self.hovered = False
        super().hideEvent(event)

    def enterEvent(self, event):
        self.hovered = True
        self.sync_timer()
        super().enterEvent(event)

    def leaveEvent(self, event):
        self.hovered = False
        self.sync_timer()
        super().leaveEvent(event)

    def eventFilter(self, obj, event):
        if event.type() in (QEvent.FocusIn, QEvent.FocusOut):
            QTimer.singleShot(0, self.sync_timer)
        return False

    def contextMenuEvent(self, event):
        self.menu_open = True
        self.sync_timer()
        menu = QMenu(self)
        style_context_menu = _module_imports.load('style_context_menu')
        style_context_menu(menu, self.window)
        menu.addAction('收起提示', lambda: self.set_expanded(False))
        try:
            menu.exec(event.globalPos())
        finally:
            menu.deleteLater()
            self.menu_open = False
            self.sync_timer()
        event.accept()
