"""Responsive dock arrangements; no workflow data is changed."""
from anclicker.platform.qt_compat.QtCore import QObject, QEvent, QTimer, Qt


def layout_band(width, font_height):
    width = width * 18 / max(18, font_height)
    return 'wide' if width >= 1200 else 'medium' if width >= 850 else 'narrow'


class ResponsiveLayout(QObject):
    def __init__(self, presets):
        super().__init__(presets.window)
        self.presets = presets
        self.last = None
        self.active_key = 'palette'
        self.applying = False
        self.timer = QTimer(self)
        self.timer.setSingleShot(True)
        self.timer.setInterval(160)
        self.timer.timeout.connect(self.apply)
        presets.window.installEventFilter(self)
        QTimer.singleShot(0, self.attach)

    def attach(self):
        docking = self.presets.view.docking
        docking.host.installEventFilter(self)
        docking.host.tabifiedDockWidgetActivated.connect(self.remember_active)
        for key in ('palette', 'controls'):
            docking.docks[key].installEventFilter(self)
        self.schedule()

    def remember_active(self, dock):
        if not self.applying and getattr(dock, 'key', None) in ('palette', 'controls'):
            self.active_key = dock.key

    def eventFilter(self, watched, event):
        if event.type() in (QEvent.Resize, QEvent.FontChange, QEvent.Show, QEvent.Hide):
            self.schedule()
        return False

    def schedule(self):
        if not self.applying and self.presets.selected == 'dynamic2':
            self.timer.start()

    def apply(self, force=False):
        p = self.presets
        if self.applying or p.selected != 'dynamic2':
            return
        v = p.view
        d = v.docking
        if d.suspended or v.compact.active:
            return
        scale = getattr(getattr(v, 'interface_scale', None), 'offset', 0)
        font_height = max(p.window.fontMetrics().height(), 18 + scale)
        band = layout_band(d.host.width(), font_height)
        panel_width = max(200, round(200 * font_height / 18))
        signature = (p.selected, band, font_height, panel_width, not d.docks['palette'].isHidden(), not d.docks['controls'].isHidden())
        if not force and signature == self.last:
            return
        self.applying = True
        previous = d.restoring
        d.restoring = True
        try:
            palette, controls = d.docks['palette'], d.docks['controls']
            visibility = {dock: not dock.isHidden() for dock in (palette, controls)}
            active = d.docks[self.active_key]
            already_tabbed = (not palette.isFloating() and not controls.isFloating()
                              and d.host.dockWidgetArea(palette) == Qt.LeftDockWidgetArea
                              and controls in d.host.tabifiedDockWidgets(palette))
            if not already_tabbed:
                for dock in (palette, controls):
                    d._set_floating(dock, False)
                    d.host.removeDockWidget(dock)
                    d.host.addDockWidget(Qt.LeftDockWidgetArea, dock)
                # Keep both switch buttons at the bottom, including wide screens.
                d.host.tabifyDockWidget(palette, controls)
                if visibility.get(active):
                    active.raise_()
                elif visibility[palette]:
                    palette.raise_()
                elif visibility[controls]:
                    controls.raise_()
            d.host.resizeDocks([palette, controls], [panel_width, panel_width], Qt.Horizontal)
            for dock, visible in visibility.items():
                if dock.isHidden() == visible:
                    dock.setVisible(visible)
                d.configure_dock(dock)
            d.update_controls_layout()
            if hasattr(d, 'scalers'):
                d.scalers[1].last_size = None
                d.scalers[1].timer.start()
            self.last = signature
        finally:
            d.restoring = previous
            self.applying = False
        d.schedule_save()
