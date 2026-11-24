"""Shared compact styling for workspace context menus."""


from anclicker.platform.qt_compat.QtCore import QObject, QEvent, QRectF, Qt
from anclicker.platform.qt_compat.QtGui import QPainter, QColor, QPen, QPalette

from anclicker._imports import DeferredImports as _DeferredImports
from anclicker.ui.file_menu_icons import file_menu_icon

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
        if event.type() in (QEvent.MouseButtonPress, QEvent.MouseButtonRelease) and event.button() == Qt.RightButton:
            if event.type() == QEvent.MouseButtonRelease:
                current = menu
                while current is not None and hasattr(current, "menuAction"):
                    current.close()
                    current = current.parentWidget()
            return True
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


def menu_workspace(owner):
    # Qt submenus are top-level windows; follow ownership to the app theme.
    widget=owner
    while widget is not None:
        workspace=getattr(widget,'view_workspace',None)
        if workspace is not None:return workspace
        widget=widget.parentWidget()
    return None


def style_context_menu(menu, owner):
    if menu.title().replace('&', '') == '帮助':
        icons = {'actionabout':'about','actionhelp':'guide','actionk':'keyboard',
                 'actionCheckForUpdates':'update'}
        for action in menu.actions():
            kind = icons.get(action.objectName())
            if kind:
                action.setIcon(file_menu_icon(kind))
                action.setIconVisibleInMenu(True)
    workspace = menu_workspace(owner)
    dark = getattr(workspace, 'theme_mode', 'light') == 'dark'
    background = '#222225' if dark else '#ffffff'
    foreground = '#f1f1f3' if dark else '#202938'
    border = '#414149' if dark else '#dfe4eb'
    hover = '#2b3e56' if dark else '#eaf3ff'
    accent = '#8bc2ff' if dark else '#1261b8'
    disabled = '#73737d' if dark else '#929ba8'
    palette=menu.palette()
    for role,color in ((QPalette.Window,background),(QPalette.Base,background),
                       (QPalette.Text,foreground),(QPalette.WindowText,foreground),
                       (QPalette.ButtonText,foreground),(QPalette.Highlight,hover),
                       (QPalette.HighlightedText,accent)):
        palette.setColor(role,QColor(color))
    palette.setColor(QPalette.Disabled,QPalette.Text,QColor(disabled))
    palette.setColor(QPalette.Disabled,QPalette.WindowText,QColor(disabled))
    menu.setPalette(palette)
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
    compact = bool(menu.property("compactFileMenu"))
    top_bar = bool(menu.property("topBarMenu"))
    font_menu=menu.title().replace('&','')=='界面字号'
    menu.setMinimumWidth(0 if compact or font_menu else (164 if top_bar else 180))
    menu.setStyleSheet(f'''
        QMenu {{ background: transparent; color: {foreground};
            border: none; border-radius: 9px; padding: 6px 10px;
            font-family: 'Microsoft YaHei UI'; font-size: 12px; }}
        QMenu::item {{ padding: 3px 18px 3px 20px; margin: 0;
            border: none; border-radius: 5px; background: transparent; }}
        QMenu::item:selected {{ background: {hover}; color: {accent}; }}
        QMenu::item:disabled {{ color: {disabled}; background: transparent; }}
        QMenu::separator {{ height: 1px; background: {border}; margin: 3px 7px; }}
        QMenu::indicator {{ width: 14px; height: 14px; }}
    ''')
    if compact:
        menu.setStyleSheet(menu.styleSheet() + '''
            QMenu { padding: 6px 10px; }
            QMenu::item { padding: 2px 8px 2px 4px; }
            QMenu::icon { left: 3px; }
            QMenu::separator { margin: 2px 4px; }
            QMenu::indicator { width: 12px; height: 12px; }
        ''')
    elif top_bar:
        menu.setStyleSheet(menu.styleSheet() + '''
            QMenu { padding: 6px 10px; }
            QMenu::item { padding: 2px 12px 2px 4px; border-radius: 5px; }
            QMenu::separator { margin: 2px 4px; }
            QMenu::indicator { width: 12px; height: 12px; }
        ''')

    if menu.property('recentRemoveMenu'):
        danger='#ff8d96' if dark else '#c53c46'
        danger_hover='#43282f' if dark else '#fff0f1'
        menu.setStyleSheet(menu.styleSheet()+f'''
            QMenu::item {{ padding: 4px 12px 4px 6px; color: {danger}; }}
            QMenu::item:selected {{ background: {danger_hover}; color: {danger}; }}
        ''')

    if font_menu:
        menu.setStyleSheet(menu.styleSheet()+'''
            QMenu::item { padding: 2px 8px 2px 4px; }
        ''')


def install_menu_styling(window):
    """Native menubar popups need the same alpha surface as context menus."""
    QMenu = _module_imports.load('QMenu')
    # Keep Qt-owned menu wrappers alive throughout styling (Qt5).
    menus = window.findChildren(QMenu)
    titles = {'文件', '界面方案', '视图', '界面字号', '设置', '帮助'}
    for menu in menus:
        parent = menu.parentWidget()
        if menu.title().replace('&', '') in titles or (isinstance(parent, QMenu) and parent.property('topBarMenu')):
            menu.setProperty('topBarMenu', True)
        if not getattr(menu, '_theme_on_show', False):
            menu._theme_on_show = True
            menu.aboutToShow.connect(lambda popup=menu: style_context_menu(popup, window))
        style_context_menu(menu, window)
