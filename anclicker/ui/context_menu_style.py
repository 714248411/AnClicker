"""Shared compact styling for workspace context menus."""


from anclicker.platform.qt_compat.QtCore import QObject, QEvent, QRectF, Qt
from anclicker.platform.qt_compat.QtGui import QPainter, QColor, QPen

from anclicker._imports import DeferredImports as _DeferredImports

# Dependencies declared here retain their existing on-demand loading boundaries.
_module_imports = _DeferredImports(globals(), {
    'QMenu': ('from', 'anclicker.platform.qt_compat.QtWidgets', ('QMenu',), 0),
})



class _RoundedMenuBackground(QObject):
    """Paint smooth alpha edges rather than a pixel-stepped window mask."""
    def __init__(self, menu, background, border):
        super().__init__(menu)
        self.background = QColor(background)
        self.border = QColor(border)
        self.border.setAlpha(180)

    def eventFilter(self, menu, event):
        if event.type() == QEvent.Type.Paint:
            painter = QPainter(menu)
            painter.setClipRegion(event.region())
            painter.setCompositionMode(QPainter.CompositionMode.CompositionMode_Source)
            painter.fillRect(menu.rect(), Qt.GlobalColor.transparent)
            painter.setCompositionMode(QPainter.CompositionMode.CompositionMode_SourceOver)
            painter.setRenderHint(QPainter.RenderHint.Antialiasing, True)
            painter.setPen(QPen(self.border, 1))
            painter.setBrush(self.background)
            painter.drawRoundedRect(QRectF(menu.rect()).adjusted(0.5, 0.5, -0.5, -0.5), 9, 9)
            painter.end()
        return super().eventFilter(menu, event)


def style_context_menu(menu, owner):
    workspace = getattr(owner.window(), 'view_workspace', None)
    dark = getattr(workspace, 'theme_mode', 'light') == 'dark'
    background = '#202024' if dark else '#ffffff'
    foreground = '#f1f1f3' if dark else '#202938'
    border = '#3b3b42' if dark else '#dfe4eb'
    hover = '#263b56' if dark else '#eaf3ff'
    accent = '#8bc2ff' if dark else '#1261b8'
    disabled = '#73737d' if dark else '#929ba8'
    menu.setWindowFlag(Qt.WindowType.FramelessWindowHint, True)
    menu.setWindowFlag(Qt.WindowType.NoDropShadowWindowHint, True)
    menu.setAttribute(Qt.WidgetAttribute.WA_TranslucentBackground, True)
    menu.setAutoFillBackground(False)
    menu.clearMask()
    if not hasattr(menu, '_rounded_menu_background'):
        menu._rounded_menu_background = _RoundedMenuBackground(menu, background, border)
        menu.installEventFilter(menu._rounded_menu_background)
    menu._rounded_menu_background.background = QColor(background)
    menu._rounded_menu_background.border = QColor(border)
    menu._rounded_menu_background.border.setAlpha(180)
    menu.setMinimumWidth(180)
    menu.setStyleSheet(f'''
        QMenu {{ background: transparent; color: {foreground};
            border: none; border-radius: 9px; padding: 6px;
            font-family: 'Microsoft YaHei UI'; font-size: 12px; }}
        QMenu::item {{ padding: 3px 18px 3px 20px; margin: 0;
            border: none; border-radius: 5px; background: transparent; }}
        QMenu::item:selected {{ background: {hover}; color: {accent}; }}
        QMenu::item:disabled {{ color: {disabled}; background: transparent; }}
        QMenu::separator {{ height: 1px; background: {border}; margin: 3px 7px; }}
        QMenu::indicator {{ width: 14px; height: 14px; }}
    ''')


def install_menu_styling(window):
    """Native menubar popups need the same alpha surface as context menus."""
    QMenu = _module_imports.load('QMenu')
    for menu in window.findChildren(QMenu):
        if not getattr(menu, '_theme_on_show', False):
            menu._theme_on_show = True
            menu.aboutToShow.connect(lambda popup=menu: style_context_menu(popup, window))
        style_context_menu(menu, window)
