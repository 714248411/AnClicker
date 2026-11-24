"""Use ordinary themed list popups, avoiding native combo menu white strips."""
from anclicker.platform.qt_compat.QtCore import Qt, QObject, QEvent, QTimer, QPoint
from anclicker.platform.qt_compat.QtGui import QColor, QPalette
from anclicker.platform.qt_compat.QtWidgets import QComboBox, QListView, QFrame

class _PopupTheme(QObject):
    def __init__(self, combo, owner):
        super().__init__(combo)
        self.combo, self.owner = combo, owner
        self.height_timer = QTimer(self)
        self.height_timer.setSingleShot(True)
        self.height_timer.timeout.connect(self.ensure_rows)
        combo.view().window().installEventFilter(self)
        self.refresh(combo.view().window())

    def eventFilter(self, watched, event):
        if event.type() == QEvent.Show:
            self.refresh(watched)
            self.ensure_rows()
            self.height_timer.start(0)
        return False

    def ensure_rows(self):
        combo = self.combo
        view = combo.view()
        popup = view.window()
        if not combo.count():
            return
        view.doItemsLayout()
        rows = min(3, combo.count())
        heights = [max(view.sizeHintForRow(i), view.fontMetrics().height()+8) for i in range(rows)]
        padding = max(0, view.height()-view.viewport().height())
        minimum = sum(heights) + padding + 2*view.frameWidth()
        view.setMinimumHeight(minimum)
        view.setMaximumHeight(16777215)
        if popup.layout() is not None:
            popup.layout().activate()
        frame = max(0, popup.height()-view.height())
        needed = minimum + frame
        if popup.height() < needed:
            popup.setMaximumHeight(16777215)
            popup.resize(popup.width(), needed)
        # Qt may initially place the menu below the field with too little room.
        screen = combo.screen().availableGeometry()
        if popup.height() <= screen.height():
            popup.move(popup.x(), max(screen.top(), min(popup.y(), screen.bottom()-popup.height()+1)))
        view.scrollTo(view.currentIndex())

    def refresh(self, watched):
        workspace = getattr(self.owner, 'view_workspace', None)
        if workspace:
            c = workspace.THEMES[workspace.theme_mode]
            palette = watched.palette()
            for role, value in ((QPalette.Window,c['surface']), (QPalette.Base,c['surface']), (QPalette.Text,c['text']), (QPalette.Highlight,c['accent']), (QPalette.HighlightedText,c['accent_text'])):
                palette.setColor(role,QColor(value))
            watched.setPalette(palette)
            watched.setAutoFillBackground(True)
            watched.setStyleSheet('background:'+c['surface']+';color:'+c['text']+';border:1px solid '+c['line']+';')
            self.combo.view().setPalette(palette)
            self.combo.view().setStyleSheet('QListView {background:'+c['surface']+';color:'+c['text']+';border:none;padding:4px;} QListView::item {min-height:26px;padding:3px 8px;border:none;} QListView::item:selected {background:'+c['accent']+';color:'+c['accent_text']+';}')

def style_settings_combos(dialog, owner):
    for combo in dialog.findChildren(QComboBox):
        if hasattr(combo,'_settings_popup_theme'):
            continue
        view = QListView(combo)
        view.setFrameShape(QFrame.NoFrame)
        view.setHorizontalScrollBarPolicy(Qt.ScrollBarAlwaysOff)
        combo.setView(view)
        combo.setMaxVisibleItems(12)
        combo.setStyleSheet(combo.styleSheet()+' QComboBox {combobox-popup:0;}')
        combo._settings_popup_theme = _PopupTheme(combo,owner)


def compact_web_combo_buttons(dialog):
    """Half-size arrow hit area while keeping readable locator text fields."""
    for combo in dialog.findChildren(QComboBox):
        if combo.property('compactWebArrow'):continue
        combo.setProperty('compactWebArrow',True)
        combo.setStyleSheet(combo.styleSheet()+'''
            QComboBox {padding-right:16px;}
            QComboBox::drop-down {subcontrol-origin:padding;subcontrol-position:center right;width:12px;height:16px;border:none;}
            QComboBox::down-arrow {width:6px;height:6px;}
        ''')
