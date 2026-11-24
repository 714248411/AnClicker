"""Shared ordering and delete menu for recording previews."""
from anclicker.platform.qt_compat.QtCore import QObject, Qt, QItemSelectionModel
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
        up=menu.addAction('上移');down=menu.addAction('下移')
        editable=bool(rows) and not view.busy and not view.written
        up.setEnabled(editable and any(row>0 and row-1 not in rows for row in rows))
        down.setEnabled(editable and any(row+1<len(view.drafts) and row+1 not in rows for row in rows))
        menu.addSeparator()
        delete = menu.addAction(f'删除选中记录（{len(rows)} 条）')
        delete.setEnabled(bool(rows) and not view.busy and not view.written)
        if view.written:
            delete.setToolTip('已写入的指令请在表格或流程图中删除')
            menu.setToolTipsVisible(True)
        try:
            chosen=menu.exec(table.viewport().mapToGlobal(position))
            if chosen==up and up.isEnabled():self.move_rows(rows,-1)
            elif chosen==down and down.isEnabled():self.move_rows(rows,1)
            elif chosen==delete and delete.isEnabled():self.delete_rows(rows)
        finally:
            menu.deleteLater()

    def move_rows(self,rows,delta):
        view=self.view
        if view.busy or view.written or delta not in (-1,1):return
        selected={row for row in rows if 0<=row<len(view.drafts)}
        for row in sorted(selected,reverse=delta>0):
            target=row+delta
            if 0<=target<len(view.drafts) and target not in selected:
                view.drafts[row],view.drafts[target]=view.drafts[target],view.drafts[row]
                selected.remove(row);selected.add(target)
        if not selected:return
        view.render_preview();table=view.preview;table.clearSelection()
        table.setCurrentCell(min(selected),0,QItemSelectionModel.NoUpdate)
        for row in sorted(selected):
            table.selectionModel().select(table.model().index(row,0),QItemSelectionModel.Select|QItemSelectionModel.Rows)
        table.scrollToItem(table.item(min(selected),0))
        view.update_buttons()
        view.status.setText('已调整录制顺序 · 尚未写入，写入时按当前预览顺序生成流程')

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
