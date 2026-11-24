"""Recent project picker and window-scoped external workbook drops."""
import os
import sqlite3
from pathlib import PureWindowsPath, PurePosixPath

from anclicker.platform.qt_compat.QtCore import QObject, QEvent, Qt, Signal, QTimer
from anclicker.platform.qt_compat.QtWidgets import QComboBox, QLineEdit, QWidget, QVBoxLayout, QLabel, QApplication, QFileDialog, QMessageBox, QMenu
from anclicker.platform.qt_compat.QtGui import QAction, QPalette, QColor
from anclicker.ui.file_menu_icons import file_menu_icon
from anclicker.platform.services import open_path
from anclicker.ui.path_drop import handles_path_drop
from anclicker.ui.context_menu_style import style_context_menu
from anclicker.ui.project_files import PROJECT_DIRECTORY, project_directory
from anclicker.storage.project_catalog import remember_project


def short_path(path):
    parsed = PureWindowsPath(path) if '\\' in path or ':' in path else PurePosixPath(path)
    parts = parsed.parts
    return ('…/' if len(parts) > 3 else '') + '/'.join(parts[-3:])


def dropped_project(mime):
    if not mime.hasUrls():
        return None
    urls = mime.urls()
    if len(urls) != 1 or not urls[0].isLocalFile():
        return None
    path = os.path.normpath(urls[0].toLocalFile())
    return path if os.path.splitext(path)[1].lower() in {'.xlsx', '.xlsm'} and os.path.isfile(path) else None


class RecentProjectPathEdit(QLineEdit):
    def createStandardContextMenu(self):
        menu = super().createStandardContextMenu()
        translations = {'Undo':'撤销', 'Redo':'重做', 'Cut':'剪切', 'Copy':'复制',
                        'Paste':'粘贴', 'Delete':'删除', 'Select All':'全选'}
        for action in menu.actions():
            label, separator, shortcut = action.text().partition('\t')
            translated = translations.get(label.replace('&', '').strip())
            if translated:
                action.setText(translated + (separator + shortcut if separator else ''))
        style_context_menu(menu, self)
        return menu

    def contextMenuEvent(self, event):
        menu = self.createStandardContextMenu()
        menu.exec(event.globalPos())
        menu.deleteLater()
        event.accept()


class RecentProjectPicker(QWidget):
    openRequested = Signal(str)
    removeRequested = Signal(str)

    def __init__(self, parent=None):
        super().__init__(parent)
        self.current_path = ''
        layout = QVBoxLayout(self)
        layout.setContentsMargins(0, 0, 0, 0)
        layout.setSpacing(3)
        label = QLabel('最近项目 · 可编辑路径 / 拖入文件', self)
        label.setContentsMargins(3, 0, 0, 0)
        label.setWordWrap(True)
        layout.addWidget(label)
        self.combo = QComboBox(self)
        self.combo.setObjectName('recentProjectsCombo')
        self.combo.setEditable(True)
        self.combo.setLineEdit(RecentProjectPathEdit(self.combo))
        self.combo.setInsertPolicy(QComboBox.NoInsert)
        self.combo.setCompleter(None)
        self.combo.setMinimumWidth(0)
        self.combo.setMinimumContentsLength(8)
        self.combo.setSizeAdjustPolicy(QComboBox.AdjustToMinimumContentsLengthWithIcon)
        self.combo.lineEdit().setPlaceholderText('输入完整 .xlsx / .xlsm 路径后按回车')
        self.combo.lineEdit().installEventFilter(self)
        self.combo.activated.connect(self._activated)
        self.combo.lineEdit().returnPressed.connect(self._typed)
        layout.addWidget(self.combo)
        self.combo.view().viewport().installEventFilter(self)
        workspace=getattr(self.window(),'view_workspace',None)
        colors=getattr(workspace,'THEMES',{}).get(getattr(workspace,'theme_mode','light'))
        if colors is not None:self.apply_theme(colors)

    def apply_theme(self,colors):
        view=self.combo.view();palette=view.palette()
        for role,key in ((QPalette.Base,'surface2'),(QPalette.Window,'surface2'),
                         (QPalette.Text,'text'),(QPalette.WindowText,'text'),
                         (QPalette.Highlight,'accent2'),(QPalette.HighlightedText,'accent_text')):
            palette.setColor(role,QColor(colors[key]))
        view.setPalette(palette);view.viewport().setPalette(palette)
        view.setStyleSheet(f"""
            QAbstractItemView {{ background:{colors['surface2']}; color:{colors['text']};
                selection-background-color:{colors['accent2']}; selection-color:{colors['accent_text']};
                border:1px solid {colors['line']}; padding:4px; outline:0; }}
            QAbstractItemView::item {{ padding:5px 8px; border:0; border-radius:5px; }}
            QAbstractItemView::item:hover {{ background:{colors['surface3']}; }}
            QAbstractItemView::item:selected {{ background:{colors['accent2']}; color:{colors['accent_text']}; }}
        """)

    def refresh(self, paths, current):
        self.current_path = current if current and current != 'None' else ''
        self.combo.blockSignals(True)
        self.combo.clear()
        unique = list(dict.fromkeys(paths))
        for path in unique:
            self.combo.addItem(short_path(path), path)
            self.combo.setItemData(self.combo.count()-1, path, Qt.ToolTipRole)
        current_key = os.path.normcase(os.path.abspath(self.current_path)) if self.current_path else ''
        selected = next((i for i, path in enumerate(unique)
                         if os.path.normcase(os.path.abspath(path)) == current_key), -1)
        self.combo.setCurrentIndex(selected)
        self.combo.setEditText(self.current_path if self.combo.lineEdit().hasFocus() else short_path(self.current_path))
        self.combo.setToolTip(self.current_path)
        self.combo.blockSignals(False)

    def _activated(self, index):
        path = self.combo.itemData(index)
        if path:
            self.combo.setEditText(path)
            self.openRequested.emit(path)

    def _typed(self):
        text = self.combo.currentText().strip().strip('"')
        # Enter can be emitted by an open popup: never interpret its abbreviated
        # label as a filesystem path or open the same project twice.
        if text == short_path(self.current_path):
            return
        if text:
            self.openRequested.emit(os.path.abspath(os.path.expanduser(os.path.expandvars(text))))

    def eventFilter(self, watched, event):
        if watched is self.combo.view().viewport() and event.type() in (QEvent.MouseButtonPress,QEvent.MouseButtonRelease) and event.button()==Qt.RightButton:
            return True
        if watched is self.combo.view().viewport() and event.type()==QEvent.ContextMenu:
            index=self.combo.view().indexAt(event.pos())
            path=self.combo.itemData(index.row()) if index.isValid() else None
            if path and recent_remove_menu(self,path,event.globalPos()):
                self.combo.hidePopup()
                QTimer.singleShot(0,lambda:self.removeRequested.emit(path))
            return True
        if event.type() == QEvent.FocusIn and self.combo.currentText() == short_path(self.current_path):
            self.combo.setEditText(self.current_path)
        elif event.type() == QEvent.FocusOut and self.combo.currentText() == self.current_path:
            QTimer.singleShot(0, lambda: self.combo.setEditText(short_path(self.current_path))
                              if not self.combo.lineEdit().hasFocus() else None)
        return False


class ProjectDropFilter(QObject):
    """Intercept only external .xlsx/.xlsm files; preserve internal instruction drags."""
    def __init__(self, window, callback):
        super().__init__(window)
        self.window, self.callback = window, callback
        for widget in [window] + window.findChildren(QWidget):
            widget.setAcceptDrops(True)
        QApplication.instance().installEventFilter(self)

    def eventFilter(self, watched, event):
        if event.type() not in (QEvent.DragEnter, QEvent.DragMove, QEvent.Drop):
            return False
        if not isinstance(watched, QWidget) or watched.window() is not self.window:
            return False
        if handles_path_drop(watched):
            return False
        if not event.mimeData().hasUrls():
            return False
        path = dropped_project(event.mimeData())
        if path:
            event.acceptProposedAction()
            if event.type() == QEvent.Drop:
                QTimer.singleShot(0, lambda: self.callback(path))
        else:
            event.ignore()
            self.window.statusBar.showMessage('请每次拖入一个 Clicker / AnClicker .xlsx / .xlsm 项目文件。', 5000)
        return True


def install_folder_import(window):
    action = QAction('导入文件夹…', window)
    action.setObjectName('actionImportProjectFolder')
    action.setIcon(file_menu_icon('folder'))
    action.setToolTip('Data 分区包含子文件夹，其他目录仅当前层')
    action.triggered.connect(lambda: import_project_folder(window))
    actions = window.menu.actions()
    index = actions.index(window.actionf) + 1
    window.menu.insertAction(actions[index] if index < len(actions) else None, action)
    window.action_import_project_folder = action
    toolbar = getattr(window, 'toolBar', None)
    if toolbar is not None and window.actionf in toolbar.actions():
        toolbar.insertAction(window.actionf, action)
        toolbar.removeAction(window.actionf)


def import_project_folder(window):
    from anclicker.app.paths import PORTABLE_DATA_FOLDER
    from anclicker.storage.data_partitions import PARTITION
    active = os.path.dirname(os.path.abspath(window.db.db_path))
    initial = active if PARTITION.fullmatch(os.path.basename(active)) else PORTABLE_DATA_FOLDER
    if window.db.get_setting_value(PROJECT_DIRECTORY):
        initial = project_directory(window.db)
    folder = QFileDialog.getExistingDirectory(window, '导入文件夹', initial)
    if not folder:
        return 0
    try:
        selected = os.path.realpath(folder)
        root = os.path.dirname(os.path.realpath(active if PARTITION.fullmatch(os.path.basename(active)) else PORTABLE_DATA_FOLDER))
        recursive = (os.path.normcase(os.path.dirname(selected)) == os.path.normcase(root)
                     and bool(PARTITION.fullmatch(os.path.basename(selected))))
        paths = []
        pending = [folder]
        visited = set()
        while pending:
            directory = pending.pop()
            identity = os.path.normcase(os.path.realpath(directory))
            if identity in visited:
                continue
            visited.add(identity)
            with os.scandir(directory) as entries:
                for entry in entries:
                    if recursive and entry.is_dir(follow_symlinks=False):
                        pending.append(entry.path)
                    elif (not entry.name.startswith('~$')
                            and os.path.splitext(entry.name)[1].lower() in {'.xlsx', '.xlsm'}
                            and entry.is_file()):
                        paths.append(entry.path)
        paths.sort(key=lambda path: (os.path.basename(path).casefold(), path))
        count = window.db.add_recent_files(paths)
        window.db.set_setting_value('最近导入项目文件夹', os.path.abspath(folder))
        window.db.set_setting_value(PROJECT_DIRECTORY, os.path.abspath(folder))
        remember_project(window.db, folder)
    except (OSError, sqlite3.Error) as error:
        QMessageBox.warning(window, '导入文件夹失败', str(error))
        return 0
    window.add_recent_to_fileMenu()
    scope = '包含所有子文件夹' if recursive else '仅当前文件夹'
    retention = '完整保留项目列表' if str(window.db.get_setting_value('项目最近文件全部保留')).lower() == 'true' else '最近项目最多保留 20 个'
    window.statusBar.showMessage(
        f'已读取 {count} 个表格文件，{retention}（{scope}）。' if count
        else f'所选文件夹没有 .xlsx / .xlsm 表格文件（{scope}）。', 6000)
    return count


def recent_remove_menu(parent,path,point):
    menu=QMenu(parent);menu.setProperty('compactFileMenu',True);menu.setProperty('recentRemoveMenu',False)
    action=menu.addAction(file_menu_icon('clear'),'删除记录')
    action.setIconVisibleInMenu(True)
    style_context_menu(menu,parent)
    action.setToolTip('只从最近列表移除，不删除磁盘文件')
    menu.setToolTipsVisible(True)
    folder_action=menu.addAction(file_menu_icon('folder'),'打开所在文件夹')
    folder_action.setIconVisibleInMenu(True)
    folder_action.setToolTip(os.path.dirname(os.path.abspath(path)))
    package_action=menu.addAction('打包为独立运行应用…')
    package_action.setEnabled(os.path.isfile(path))
    package_action.setToolTip('打包已保存项目，打开即运行；仅保留退出及暂停/恢复快捷键')
    try:
        selected=menu.exec(point)
        if selected is package_action:
            from anclicker.ui.standalone_export import export_recent_application
            if isinstance(parent, RecentProjectPicker):parent.combo.hidePopup()
            elif isinstance(parent, QMenu):
                current=parent
                while isinstance(current,QMenu):
                    current.hide();current=current.parentWidget()
            QTimer.singleShot(0,lambda:export_recent_application(parent,path))
        if selected is folder_action:
            if isinstance(parent, RecentProjectPicker):
                parent.combo.hidePopup()
            elif isinstance(parent, QMenu):
                parent.hide()
            QTimer.singleShot(0,lambda:open_recent_folder(parent,path))
        return selected is action
    finally:menu.deleteLater()


def open_recent_folder(parent,path):
    folder=os.path.dirname(os.path.abspath(path))
    if not os.path.isdir(folder):
        QMessageBox.warning(parent,'打开文件夹','所在文件夹不存在。')
        return False
    try:
        open_path(folder)
        return True
    except OSError as error:
        QMessageBox.warning(parent,'打开文件夹失败',str(error))
        return False


class RecentMenuFilter(QObject):
    def __init__(self,window):
        super().__init__(window.menuzv);self.window=window
        window.menuzv.installEventFilter(self)

    def eventFilter(self,watched,event):
        if event.type() in (QEvent.MouseButtonPress,QEvent.MouseButtonRelease) and event.button()==Qt.RightButton:return True
        if event.type()!=QEvent.ContextMenu:return False
        action=watched.actionAt(event.pos());path=action.data() if action else None
        if path and recent_remove_menu(watched,path,event.globalPos()):
            watched.hide()
            QTimer.singleShot(0,lambda:self.window.remove_recent_project(path))
        return True


def install_recent_context_menu(window):
    if not hasattr(window.menuzv,'_recent_remove_filter'):
        window.menuzv._recent_remove_filter=RecentMenuFilter(window)
