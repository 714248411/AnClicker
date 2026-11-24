"""Per-window typography and icon sizing, including newly opened dialogs."""
import re
import weakref
from anclicker.platform.qt_compat.QtCore import QObject, QEvent, QTimer, QSize
from anclicker.platform.qt_compat.QtWidgets import QApplication, QWidget, QAbstractButton, QToolBar, QMessageBox, QDialogButtonBox


def original_style(widget):
    record = getattr(widget, '_interface_style', None)
    current = widget.styleSheet()
    return record[0] if record and current == record[1] else current


class InterfaceScale(QObject):
    def __init__(self, window):
        super().__init__(window)
        self.window = window
        try:
            self.offset = max(-5, min(10, int(window.db.get_setting_value('界面字号偏移') or 0)))
        except (ValueError, TypeError):
            self.offset = 0
        self.busy = False
        self.applied = False
        self.listening = False
        self.widgets = weakref.WeakKeyDictionary()
        self.timer = QTimer(self)
        self.timer.setSingleShot(True)
        self.timer.timeout.connect(self.apply)
        QApplication.instance().aboutToQuit.connect(self.stop)
        QTimer.singleShot(0, self.start)

    def stop(self):
        self.timer.stop()
        self.listen(False)

    def start(self):
        self.listen(True)
        self.apply()

    def listen(self, enabled):
        if enabled == self.listening: return
        app = QApplication.instance()
        if enabled: app.installEventFilter(self)
        else: app.removeEventFilter(self)
        self.listening = enabled

    def owns(self, widget):
        while widget is not None:
            if widget is self.window or getattr(widget, '_workspace_owner', None) is self.window:
                return True
            widget = widget.parent()
        return False

    def eventFilter(self, obj, event):
        if event.type() == QEvent.Show and isinstance(obj, (QMessageBox, QDialogButtonBox)) and self.owns(obj):
            labels = {QMessageBox.Yes:'是', QMessageBox.No:'否', QMessageBox.Ok:'确定',
                      QMessageBox.Cancel:'取消', QMessageBox.YesToAll:'全部是', QMessageBox.NoToAll:'全部否',
                      QMessageBox.Close:'关闭', QMessageBox.Save:'保存', QMessageBox.Discard:'放弃',
                      QMessageBox.Apply:'应用', QMessageBox.Reset:'重置', QMessageBox.Retry:'重试',
                      QMessageBox.Abort:'终止', QMessageBox.Ignore:'忽略', QMessageBox.Help:'帮助'}
            def translate_buttons():
                for standard, text in labels.items():
                    button = obj.button(QDialogButtonBox.StandardButton(int(standard)) if isinstance(obj, QDialogButtonBox) else standard)
                    if button is not None: button.setText(text)
            translate_buttons()
            if not hasattr(obj, '_chinese_button_timer'):
                obj._chinese_button_timer = QTimer(obj)
                obj._chinese_button_timer.setSingleShot(True)
                obj._chinese_button_timer.timeout.connect(translate_buttons)
            obj._chinese_button_timer.start(0)
            if isinstance(obj, QMessageBox):
                from anclicker.ui.settings_theme import apply_settings_theme
                apply_settings_theme(obj, self.window)
        if not self.busy and event.type() in (QEvent.Show, QEvent.StyleChange):
            # Do not inspect partially constructed native children in event filters.
            if not self.timer.isActive():
                self.timer.start(0)
        return False

    def change(self, amount=None):
        self.offset = 0 if amount is None else max(-5, min(10, self.offset + amount))
        self.window.db.set_setting_value('界面字号偏移', str(self.offset))
        self.listen(True)
        self.apply()
        workspace = getattr(self.window, 'view_workspace', None)
        presets = getattr(workspace, 'layout_presets', None)
        if presets is not None:
            presets.view.docking.refresh_control_actions_style()
            presets.responsive.schedule()

    def stylesheet(self, text):
        delta = self.offset
        if not delta:
            return text
        text = re.sub(r'(font-size\s*:\s*)(\d+(?:\.\d+)?)(px|pt)',
                      lambda m: m[1] + str(max(7, round(float(m[2]) + delta))) + m[3], text)
        # Checkbox/radio indicators are the icon equivalent of text glyphs.
        def indicator(match):
            return re.sub(r'((?:width|height)\s*:\s*)(\d+(?:\.\d+)?)px',
                          lambda m: m[1] + str(max(6, round(float(m[2]) * (1 + delta / 13)))) + 'px', match[0])
        return re.sub(r'[^{}]*::indicator[^{}]*\{[^{}]*\}', indicator, text)

    def apply(self):
        if self.busy or (self.offset == 0 and not self.applied):
            return
        self.busy = True
        try:
            widgets = [w for w in QApplication.allWidgets() if self.owns(w)]
            # Parent first prevents inherited font changes becoming child defaults.
            def depth(w):
                n = 0
                while w.parent() is not None:
                    n += 1; w = w.parent()
                return n
            widgets.sort(key=depth)
            for w in widgets:
                state = self.widgets.setdefault(w, {})
                base = original_style(w)
                ancestor = w
                while ancestor is not None and not ancestor.property('uniformSettingsFont'):
                    ancestor = ancestor.parentWidget() if isinstance(ancestor, QWidget) else None
                if ancestor is not None:
                    base = re.sub(r'font-size\s*:\s*\d+(?:\.\d+)?(?:px|pt)', 'font-size:'+str(getattr(getattr(ancestor, '_panel_scaler', None), 'last_size', None) or 14)+'px', base)
                scaled = self.stylesheet(base)
                w._interface_style = (base, scaled)
                if w.styleSheet() != scaled:
                    w.setStyleSheet(scaled)
                if isinstance(w, (QAbstractButton, QToolBar)):
                    current = w.iconSize()
                    if 'icon' not in state or current != state['icon_output']:
                        state['icon'] = QSize(current)
                    icon = state['icon']
                    factor = 1 + self.offset / 13
                    output = QSize(max(6, round(icon.width() * factor)), max(6, round(icon.height() * factor)))
                    state['icon_output'] = output
                    if current != output:
                        w.setIconSize(output)
            workspace = getattr(self.window, "view_workspace", None)
            if workspace is not None and not getattr(getattr(workspace, "compact", None), "active", False):
                workspace._align_search_row()
                status = self.window.statusBar
                status.setFixedHeight(max(18, status.fontMetrics().height() + 2))
        finally:
            self.applied = self.offset != 0
            self.busy = False
