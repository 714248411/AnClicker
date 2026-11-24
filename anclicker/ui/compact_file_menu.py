"""Compact file menus with full-text hover hints for elided entries."""
from anclicker.platform.qt_compat.QtCore import QObject, QEvent, Qt
from anclicker.ui.file_menu_icons import file_menu_icon


def elide_with_dots(metrics, text, width):
    if metrics.horizontalAdvance(text) <= width:
        return text
    prefix = text
    while prefix and metrics.horizontalAdvance(prefix + '...') > width:
        prefix = prefix[:-1]
    return prefix + '...'


class CompactFileMenu(QObject):
    def __init__(self, menu, *, paths=False):
        super().__init__(menu)
        self.menu = menu
        self.paths = paths
        menu.setProperty('compactFileMenu', True)
        menu.setToolTipsVisible(True)
        menu.setStyleSheet(menu.styleSheet() + '''
            QMenu[compactFileMenu="true"] { padding: 6px 10px; }
            QMenu[compactFileMenu="true"]::item {
                padding: 2px 8px 2px 4px; margin: 0; border-radius: 5px;
            }
            QMenu[compactFileMenu="true"]::icon { left: 3px; }
            QMenu[compactFileMenu="true"]::separator { height: 1px; margin: 3px 4px; }
        ''')
        menu.aboutToShow.connect(self.refresh)
        menu.installEventFilter(self)

    def refresh(self):
        metrics = self.menu.fontMetrics()
        # Main entries share a narrow label column beside the shortcut column;
        # recent paths have no shortcuts, so allow a wider readable column.
        width = metrics.horizontalAdvance('文' * 22 if self.paths else '导出整体数据…')
        shortcut_width = metrics.horizontalAdvance('Ctrl+N')
        screen = self.menu.screen()
        if screen is not None:
            width = min(width, max(80, screen.availableGeometry().width() - 140))
        for action in self.menu.actions():
            if action.isSeparator():
                continue
            if not self.paths:
                kind = {'actionNewBlankPage':'new','actionx':'save','actiona':'save_as',
                        'actionf':'import','actionImportProjectFolder':'folder'}.get(action.objectName())
                if action.menu() is not None:
                    kind = 'recent'
                if kind:
                    action.setIcon(file_menu_icon(kind))
                    action.setIconVisibleInMenu(True)
            full = action.property('compactFullText')
            if full is None:
                full = action.text()
                action.setProperty('compactFullText', full)
            text = (metrics.elidedText(full, Qt.ElideMiddle, width) if self.paths
                    else elide_with_dots(metrics, full, width))
            shortcut = action.shortcut().toString()
            abbreviated = elide_with_dots(metrics, shortcut, shortcut_width)
            action.setText(text + ('\t' + abbreviated if shortcut else ''))
            hint = full + ('  (' + shortcut + ')' if shortcut else '')
            action.setToolTip(hint if text != full or abbreviated != shortcut else '')
            action.setStatusTip(hint)

    def eventFilter(self, watched, event):
        if event.type() == QEvent.FontChange:
            self.refresh()
        return False


def install_compact_file_menus(window):
    for menu, paths in ((window.menu, False), (getattr(window, 'menuzv', None), True)):
        if menu is not None and not hasattr(menu, '_compact_file_controller'):
            menu._compact_file_controller = CompactFileMenu(menu, paths=paths)
