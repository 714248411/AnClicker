"""Persistent menu shortcuts; Qt's toolbar extension handles limited space."""
import json
from qt_compat.QtCore import QObject, QEvent, QTimer, Qt
from qt_compat.QtGui import QAction
from qt_compat.QtWidgets import QMenu, QToolButton

SETTING = '工具栏自选功能'

class ToolbarCustomization(QObject):
    ROOTS = {'文件', '界面方案', '视图', '界面字号', '工具', '检查更新'}

    def __init__(self, window):
        super().__init__(window)
        self.window, self.toolbar = window, window.toolBar
        self.sources, self.proxies = {}, {}
        self.watched = set()
        try:
            saved = json.loads(window.db.get_setting_value(SETTING) or '[]')
        except (ValueError, TypeError):
            saved = []
        self.selected = list(dict.fromkeys(x for x in saved if isinstance(x, str))) if isinstance(saved, list) else []
        self.timer = QTimer(self)
        self.timer.setSingleShot(True)
        self.timer.timeout.connect(self.sync)
        self.menu = QMenu('添加工具', self.toolbar)
        self.menu.aboutToShow.connect(self.populate)
        self.add_action = self.toolbar.addAction('添加工具')
        self.add_action.setMenu(self.menu)
        self.add_action.setToolTip('勾选要放入工具栏的菜单功能；取消勾选即可移除')
        button = self.toolbar.widgetForAction(self.add_action)
        button.setPopupMode(QToolButton.ToolButtonPopupMode.InstantPopup)
        from toolbar_reorder import ToolbarReorder
        self.reorder = ToolbarReorder(window, self.add_action)
        self.watch(window.menubar)
        self.sync()

    @staticmethod
    def label(action):
        return action.text().replace('&', '').split('\t')[0]

    def watch(self, widget):
        if widget not in self.watched:
            self.watched.add(widget)
            widget.installEventFilter(self)
            widget.destroyed.connect(lambda *_: self.watched.discard(widget))

    def eventFilter(self, obj, event):
        if event.type() in (QEvent.Type.ActionAdded, QEvent.Type.ActionRemoved, QEvent.Type.ActionChanged):
            self.timer.start(0)
        return False

    def collect(self):
        sources = {}
        def walk(menu, path, labels):
            self.watch(menu)
            for action in menu.actions():
                if action.isSeparator():
                    continue
                label = self.label(action)
                key = path + '/' + (action.objectName() or label)
                if action.menu():
                    walk(action.menu(), key, labels + [label])
                else:
                    sources[key] = (action, labels)
        for action in self.window.menubar.actions():
            label = self.label(action)
            if action.menu() and label in self.ROOTS:
                walk(action.menu(), label, [label])
            elif label == '检查更新':
                sources[label] = (action, ['检查更新'])
            elif action.menu():
                # Some versions place update checking inside Help.
                self.watch(action.menu())
                for child in action.menu().actions():
                    if self.label(child) == '检查更新':
                        sources['检查更新'] = (child, ['检查更新'])
        return sources

    def sync(self):
        self.sources = self.collect()
        wanted = [key for key in self.selected if key in self.sources]
        for key in list(self.proxies):
            if key not in wanted:
                proxy = self.proxies.pop(key)
                self.toolbar.removeAction(proxy)
                proxy.deleteLater()
        for key in wanted:
            source = self.sources[key][0]
            if key not in self.proxies:
                proxy = QAction(self.toolbar)
                proxy.triggered.connect(lambda checked=False, k=key: self.trigger(k))
                proxy.setProperty('toolbarOrderId', 'menu:' + key)
                self.proxies[key] = proxy
                self.toolbar.insertAction(self.add_action, proxy)
            proxy = self.proxies[key]
            proxy.setText(source.text())
            proxy.setIcon(source.icon())
            proxy.setToolTip(source.toolTip())
            proxy.setEnabled(source.isEnabled())
            proxy.setVisible(source.isVisible())
            proxy.setCheckable(source.isCheckable())
            proxy.setChecked(source.isChecked())
            self.toolbar.widgetForAction(proxy).setToolButtonStyle(Qt.ToolButtonStyle.ToolButtonTextOnly)

        self.reorder.refresh()

    def trigger(self, key):
        self.sync()
        if key in self.sources:
            self.sources[key][0].trigger()
        self.sync()

    def select(self, key, enabled):
        if enabled and key not in self.selected:
            self.selected.append(key)
        elif not enabled and key in self.selected:
            self.selected.remove(key)
        self.window.db.set_setting_value(SETTING, json.dumps(self.selected, ensure_ascii=False))
        self.sync()

    def populate(self):
        self.sync()
        self.menu.clear()
        groups = {(): self.menu}
        for key, (source, labels) in self.sources.items():
            path = ()
            for label in labels:
                next_path = path + (label,)
                if next_path not in groups:
                    groups[next_path] = groups[path].addMenu(label)
                path = next_path
            choice = groups[path].addAction(source.text())
            choice.setCheckable(True)
            choice.setChecked(key in self.selected)
            choice.toggled.connect(lambda checked, k=key: self.select(k, checked))
        if self.selected:
            self.menu.addSeparator()
            clear = self.menu.addAction('清空自选工具')
            clear.triggered.connect(self.clear)

    def clear(self):
        self.selected.clear()
        self.window.db.set_setting_value(SETTING, '[]')
        self.sync()
