"""Searchable, draggable instruction palette."""

from __future__ import annotations

from PySide6.QtCore import QMimeData, QPoint, Signal, Qt
from PySide6.QtGui import QDrag
from PySide6.QtWidgets import (
    QAbstractItemView,
    QLineEdit,
    QTreeWidget,
    QTreeWidgetItem,
    QVBoxLayout,
    QWidget,
)

from node_editor.specs import NodeDisplaySpec, normalize_specs


INSTRUCTION_MIME_TYPE = "application/x-clicker-instruction"
TYPE_ID_ROLE = Qt.ItemDataRole.UserRole


class _InstructionTree(QTreeWidget):
    instructionActivated = Signal(str)

    def __init__(self, parent_=None):
        super().__init__(parent_)
        self._drag_start = QPoint()
        self.setHeaderHidden(True)
        self.setIndentation(16)
        self.setDragEnabled(True)
        self.setSelectionMode(QAbstractItemView.SelectionMode.SingleSelection)
        self.itemDoubleClicked.connect(self._activate_item)

    @staticmethod
    def instruction_type(item_) -> str | None:
        if item_ is None:
            return None
        value_ = item_.data(0, TYPE_ID_ROLE)
        return str(value_) if value_ not in (None, "") else None

    def _activate_item(self, item_, column_):
        del column_
        type_id_ = self.instruction_type(item_)
        if type_id_ is not None:
            self.instructionActivated.emit(type_id_)

    def mousePressEvent(self, event_):
        if event_.button() == Qt.MouseButton.LeftButton:
            self._drag_start = event_.position().toPoint()
        super().mousePressEvent(event_)

    def mouseMoveEvent(self, event_):
        if not event_.buttons() & Qt.MouseButton.LeftButton:
            super().mouseMoveEvent(event_)
            return
        if (event_.position().toPoint() - self._drag_start).manhattanLength() < 8:
            super().mouseMoveEvent(event_)
            return

        type_id_ = self.instruction_type(self.currentItem())
        if type_id_ is None:
            super().mouseMoveEvent(event_)
            return

        mime_data_ = QMimeData()
        mime_data_.setData(INSTRUCTION_MIME_TYPE, type_id_.encode("utf-8"))
        drag_ = QDrag(self)
        drag_.setMimeData(mime_data_)
        drag_.exec(Qt.DropAction.CopyAction)


class InstructionPalette(QWidget):
    """Search field and categorized instruction tree built from registry specs."""

    instructionActivated = Signal(str)
    instructionDoubleClicked = Signal(str)

    def __init__(self, specs_=None, parent_=None):
        super().__init__(parent_)
        self.search_edit = QLineEdit(self)
        self.search_edit.setObjectName("instructionSearchEdit")
        self.search_edit.setPlaceholderText("搜索指令...")
        self.tree = _InstructionTree(self)
        self.tree.setObjectName("instructionTree")

        layout_ = QVBoxLayout(self)
        layout_.setContentsMargins(0, 0, 0, 0)
        layout_.setSpacing(6)
        layout_.addWidget(self.search_edit)
        layout_.addWidget(self.tree, 1)

        self._specs: dict[str, NodeDisplaySpec] = {}
        self.search_edit.textChanged.connect(self._apply_filter)
        self.tree.instructionActivated.connect(self._emit_activation)
        self.set_specs(specs_ or {})

    def _emit_activation(self, type_id_) -> None:
        self.instructionActivated.emit(type_id_)
        self.instructionDoubleClicked.emit(type_id_)

    def set_specs(self, specs_) -> None:
        self._specs = normalize_specs(specs_)
        self.tree.clear()
        categories_: dict[str, QTreeWidgetItem] = {}
        for spec_ in self._specs.values():
            category_item_ = categories_.get(spec_.category)
            if category_item_ is None:
                category_item_ = QTreeWidgetItem([spec_.category])
                category_item_.setFlags(
                    category_item_.flags() & ~Qt.ItemFlag.ItemIsDragEnabled
                )
                self.tree.addTopLevelItem(category_item_)
                categories_[spec_.category] = category_item_

            instruction_item_ = QTreeWidgetItem([spec_.title])
            instruction_item_.setData(0, TYPE_ID_ROLE, spec_.type_id)
            instruction_item_.setForeground(0, spec_.color.lighter(150))
            category_item_.addChild(instruction_item_)
        self.tree.expandAll()
        self._apply_filter(self.search_edit.text())

    def specs(self) -> dict[str, NodeDisplaySpec]:
        return dict(self._specs)

    def selected_type_id(self) -> str | None:
        """Return the selected instruction leaf's type id, if any."""

        return self.tree.instruction_type(self.tree.currentItem())

    def _apply_filter(self, filter_text_) -> None:
        needle_ = filter_text_.strip().casefold()
        for category_index_ in range(self.tree.topLevelItemCount()):
            category_item_ = self.tree.topLevelItem(category_index_)
            category_match_ = needle_ in category_item_.text(0).casefold()
            any_visible_ = False
            for child_index_ in range(category_item_.childCount()):
                instruction_item_ = category_item_.child(child_index_)
                visible_ = category_match_ or needle_ in instruction_item_.text(0).casefold()
                instruction_item_.setHidden(not visible_)
                any_visible_ = any_visible_ or visible_
            category_item_.setHidden(not any_visible_)
            if any_visible_ and needle_:
                category_item_.setExpanded(True)
