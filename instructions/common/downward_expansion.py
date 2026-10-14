"""Expand instruction options below existing fields without moving the window top."""
from qt_compat.QtCore import QObject, QTimer
from qt_compat.QtWidgets import QDockWidget, QScrollArea


class DownwardExpansion(QObject):
    def __init__(self, editor, panel):
        super().__init__(editor)
        self.editor, self.panel = editor, panel
        self.expanded = False
        self.saved = None
        self.fixed = []

    @property
    def root_layout(self):
        ui = getattr(self.editor, "ui", None)
        return ui.rootLayout if ui is not None else self.editor.layout()

    def setExpanded(self, expanded):
        expanded = bool(expanded)
        if expanded == self.expanded:
            return
        self.expanded = expanded
        outer = self.editor.window()
        floating = outer is self.editor or (isinstance(outer, QDockWidget) and outer.isFloating())
        scaler = getattr(self.editor, '_panel_scaler', None)
        if expanded:
            self.saved = (outer, outer.size(), floating)
            self.scroll_positions = [(area.verticalScrollBar(), area.verticalScrollBar().value())
                                     for area in outer.findChildren(QScrollArea)]
            # Freeze preceding sections at their current height; options must not squeeze them.
            layout = self.root_layout
            branch = self.panel
            while branch.parentWidget() is not None and layout.indexOf(branch) < 0:
                branch = branch.parentWidget()
            index = layout.indexOf(branch)
            self.fixed = []
            for i in range(max(0, index)):
                widget = layout.itemAt(i).widget()
                if widget is not None and widget.isVisible():
                    self.fixed.append((widget, widget.minimumHeight(), widget.maximumHeight()))
                    widget.setFixedHeight(widget.height())
            if scaler is not None and scaler.last_size is not None:
                scaler.expanded_pixels = scaler.last_size
        else:
            for widget, minimum, maximum in self.fixed:
                widget.setMinimumHeight(minimum)
                widget.setMaximumHeight(maximum)
            self.fixed = []
        self.panel.setVisible(expanded)
        self.root_layout.invalidate()
        QTimer.singleShot(0, self._resize)

    def _resize(self):
        if self.saved is None:
            return
        outer, size, floating = self.saved
        self.root_layout.activate()
        if floating and (outer is self.editor or (isinstance(outer, QDockWidget) and outer.isFloating())):
            height = size.height()
            if self.expanded:
                extra = self.panel.sizeHint().height() + self.root_layout.spacing()
                room = max(0, outer.screen().availableGeometry().bottom()-outer.y()+1-height)
                height += min(extra, room)
            outer.resize(size.width(), height)
        for bar, value in self.scroll_positions:
            bar.setValue(value)
        if not self.expanded:
            scaler = getattr(self.editor, '_panel_scaler', None)
            if scaler is not None:
                if hasattr(scaler, 'expanded_pixels'):
                    del scaler.expanded_pixels
                scaler.timer.start()
