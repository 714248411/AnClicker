"""Scale dense side panels only after their usual layout runs out of room."""
import re

from qt_compat.QtCore import QObject, QEvent, QTimer
from qt_compat.QtWidgets import QWidget, QLayout


class AdaptivePanelSizer(QObject):
    def __init__(self, viewport, body, reference_width, palette=False, reference_height=340):
        super().__init__(body)
        self.viewport, self.body, self.reference_width = viewport, body, reference_width
        self.palette = palette
        self.reference_height = reference_height
        self.base_style = body.styleSheet()
        self.last_size = None
        self.minimums = {}
        self.layout_metrics = {}
        self.child_styles = {}
        self.timer = QTimer(self); self.timer.setSingleShot(True); self.timer.setInterval(0)
        self.timer.timeout.connect(self.apply)
        viewport.installEventFilter(self)
        QTimer.singleShot(0, self.apply)

    def rebind(self, viewport):
        self.viewport.removeEventFilter(self)
        self.viewport = viewport
        viewport.installEventFilter(self)
        self.last_size = None
        self.timer.start()

    def eventFilter(self, watched, event):
        if event.type() in (QEvent.Resize, QEvent.Show): self.timer.start()
        return False

    def apply(self):
        view = self.body.window()
        # The compact console has its own proportional stylesheet.
        if getattr(getattr(getattr(view, 'view_workspace', None), 'compact', None), 'active', False): return
        width, height = self.viewport.width(), self.viewport.height()
        if width <= 0 or height <= 0: return
        ratio = min(1.0, width / self.reference_width)
        if not self.palette:
            horizontal = bool(self.body.property('horizontalControls'))
            ratio = min(1.0, width / (460 if horizontal else self.reference_width), height / (190 if horizontal else self.reference_height))
        pixels = max(7, round(13 * ratio))
        if pixels == self.last_size: return
        self.last_size = pixels
        scale = pixels / 13
        for child in self.body.findChildren(QWidget):
            if child not in self.minimums: self.minimums[child] = child.minimumSize()
            if child not in self.child_styles: self.child_styles[child] = child.styleSheet()
            original_style = self.child_styles[child]
            if 'font-size' in original_style:
                child.setStyleSheet(re.sub(r'font-size\s*:\s*(\d+(?:\.\d+)?)(px|pt)',
                    lambda match: 'font-size: '+str(max(7,round(float(match.group(1))*scale)))+match.group(2),original_style))
            size = self.minimums[child]
            child.setMinimumSize(round(size.width()*scale), round(size.height()*scale))
        for layout in self.body.findChildren(QLayout):
            if layout not in self.layout_metrics:
                margins=layout.contentsMargins()
                self.layout_metrics[layout]=((margins.left(),margins.top(),margins.right(),margins.bottom()),layout.spacing())
            margins,spacing=self.layout_metrics[layout]
            layout.setContentsMargins(*(round(x*scale) for x in margins))
            if spacing>=0:layout.setSpacing(max(1,round(spacing*scale)))
        pad = max(1, round(6*scale))
        indicator = max(8, round(16*scale))
        self.body.setStyleSheet(self.base_style + f'''
            QWidget {{ font-size: {pixels}px; }}
            QPushButton, QToolButton, QLineEdit, QSpinBox, QDoubleSpinBox, QComboBox {{ padding: {pad}px; min-height: 0px; }}
            QCheckBox, QRadioButton {{ spacing: {max(2,round(7*scale))}px; padding: {max(0,round(3*scale))}px; }}
            QCheckBox::indicator, QRadioButton::indicator {{ width: {indicator}px; height: {indicator}px; }}
            QTreeWidget::item {{ padding: {max(1,round(5*scale))}px; }}
            QLineEdit#instructionSearchEdit {{ padding: 1px 3px; }}
        ''')
        if self.palette:
            from qt_compat.QtWidgets import QTreeWidget
            tree = self.body.findChild(QTreeWidget)
            if tree:
                tree.setIndentation(max(8,round(16*scale)))
                tree.scheduleDelayedItemsLayout()
