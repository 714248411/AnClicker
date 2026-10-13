"""Use ordinary themed list popups, avoiding native combo menu white strips."""
from qt_compat.QtCore import Qt, QObject, QEvent
from qt_compat.QtGui import QColor, QPalette
from qt_compat.QtWidgets import QComboBox, QListView, QFrame

class _PopupTheme(QObject):
    def __init__(self, combo, owner):
        super().__init__(combo)
        self.combo, self.owner = combo, owner
        combo.view().window().installEventFilter(self)
        self.refresh(combo.view().window())

    def eventFilter(self, watched, event):
        if event.type() == QEvent.Show:
            self.refresh(watched)
        return False

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
