"""Shared delete menu for recording previews."""
from anclicker.platform.qt_compat.QtCore import QObject, Qt
from anclicker.platform.qt_compat.QtWidgets import QAbstractItemView, QMenu, QMessageBox
from anclicker.ui.context_menu_style import style_context_menu


class RecordingPreviewMenu(QObject):
    def __init__(self, view):
        super().__init__(view)
        self.view = view
        table = view.preview
        table.setSelectionBehavior(QAbstractItemView.SelectionBehavior.SelectRows)
        table.setSelectionMode(QAbstractItemView.SelectionMode.ExtendedSelection)
        table.setContextMenuPolicy(Qt.ContextMenuPolicy.CustomContextMenu)
        table.customContextMenuRequested.connect(self.show_menu)

    def show_menu(self, position):
        view = self.view
        table = view.preview
        index = table.indexAt(position)
        if index.isValid() and not table.selectionModel().isSelected(index):
            table.clearSelection()
            table.selectRow(index.row())
        rows = sorted({index.row() for index in table.selectedIndexes()})
        menu = QMenu(table)
        style_context_menu(menu, view)
        delete = menu.addAction(f'删除选中记录（{len(rows)} 条）')
        delete.setEnabled(bool(rows) and not view.busy and not view.written)
        if view.written:
            delete.setToolTip('已写入的指令请在表格或流程图中删除')
            menu.setToolTipsVisible(True)
        try:
            if menu.exec(table.viewport().mapToGlobal(position)) == delete and delete.isEnabled():
                self.delete_rows(rows)
        finally:
            menu.deleteLater()

    def delete_rows(self, rows):
        view = self.view
        if view.busy or view.written:
            return
        rows = {row for row in rows if 0 <= row < len(view.drafts)}
        if not rows:
            return
        confirm = QMessageBox(view)
        confirm.setWindowTitle('删除录制记录')
        confirm.setText(f'确认删除选中的 {len(rows)} 条录制记录？')
        confirm.setStandardButtons(QMessageBox.StandardButton.Ok | QMessageBox.StandardButton.Cancel)
        confirm.button(QMessageBox.StandardButton.Ok).setText('确认')
        confirm.button(QMessageBox.StandardButton.Cancel).setText('取消')
        confirm.setDefaultButton(QMessageBox.StandardButton.Ok)
        confirm.setEscapeButton(QMessageBox.StandardButton.Cancel)
        if confirm.exec() != QMessageBox.StandardButton.Ok:
            return
        if view.busy or view.written:
            return
        view.drafts = [draft for row, draft in enumerate(view.drafts) if row not in rows]
        view.render_preview()
        view.update_buttons()
        view.status.setText(f'已删除 {len(rows)} 条记录 · 剩余 {len(view.drafts)} 条（尚未写入）')
