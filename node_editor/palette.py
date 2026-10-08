"""Searchable, draggable instruction palette."""

from __future__ import annotations

from qt_compat.QtCore import QMimeData, QPoint, Signal, Qt
from qt_compat.QtGui import QDrag
from qt_compat.QtWidgets import (
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
        self.setMouseTracking(True)
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
    quickCaptureRequested = Signal()
    quickOcrCaptureRequested = Signal()

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
        self.tree.itemClicked.connect(self._quick_action_clicked)
        self.set_specs(specs_ or {})

    def _quick_action_clicked(self, item, column):
        if item is self._quick_capture_item:
            self.quickCaptureRequested.emit()
        elif item is self._quick_ocr_item:
            self.quickOcrCaptureRequested.emit()

    def _emit_activation(self, type_id_) -> None:
        self.instructionActivated.emit(type_id_)
        self.instructionDoubleClicked.emit(type_id_)

    def set_specs(self, specs_) -> None:
        self._specs = normalize_specs(specs_)
        self._capture_item = None
        self.tree.clear()
        self._quick_group = QTreeWidgetItem(['快捷功能栏'])
        self._quick_group.setFlags(self._quick_group.flags() & ~Qt.ItemFlag.ItemIsDragEnabled)
        self.tree.addTopLevelItem(self._quick_group)
        self._quick_capture_item = QTreeWidgetItem(['快捷截图（吸附边缘）'])
        self._quick_capture_item.setFlags(self._quick_capture_item.flags() & ~Qt.ItemFlag.ItemIsDragEnabled)
        self._quick_capture_item.setToolTip(0, '单击截图；完成后拖入“点击快捷截图”，组合成图像点击指令。')
        self._quick_group.addChild(self._quick_capture_item)
        self._quick_ocr_item = QTreeWidgetItem(['快捷截图（OCR）'])
        self._quick_ocr_item.setFlags(self._quick_ocr_item.flags() & ~Qt.ItemFlag.ItemIsDragEnabled)
        self._quick_ocr_item.setToolTip(0, '框选范围后选择点击识别区域或复制文字，确认后加入流程。')
        self._quick_group.addChild(self._quick_ocr_item)
        categories_: dict[str, QTreeWidgetItem] = {}
        ocr_shortcuts = ('OCR文字提取', 'OCR复制', 'OCR粘贴', 'OCR点击识别区域')
        for spec_ in self._specs.values():
            # Display groups do not change persisted type IDs or import paths.
            category = ('离线OCR' if spec_.category == '本地OCR' else
                        'OCR' if spec_.type_id == 'OCR识别' else spec_.category)
            category_item_ = categories_.get(category)
            if category_item_ is None:
                category_item_ = QTreeWidgetItem([category])
                category_item_.setFlags(
                    category_item_.flags() & ~Qt.ItemFlag.ItemIsDragEnabled
                )
                self.tree.addTopLevelItem(category_item_)
                categories_[category] = category_item_

            instruction_item_ = QTreeWidgetItem([spec_.title])
            instruction_item_.setData(0, TYPE_ID_ROLE, spec_.type_id)
            category_item_.addChild(instruction_item_)
        # Keep the original directory and stable command IDs. Common actions
        # lead the list once, followed by the more specialized OCR commands.
        offline_group = categories_.get('离线OCR')
        if offline_group is not None:
            for position, kind in enumerate(ocr_shortcuts):
                item = next((offline_group.child(i) for i in range(offline_group.childCount())
                             if offline_group.child(i).data(0, TYPE_ID_ROLE) == kind), None)
                if item is None:
                    continue
                offline_group.takeChild(offline_group.indexOfChild(item))
                offline_group.insertChild(position, item)
                if kind == 'OCR点击识别区域':
                    item.setText(0, 'OCR点击')
                    item.setToolTip(0, '识别并点击文字区域；可设置目标文字、范围及第几个结果。')
        self.tree.expandAll()
        self._apply_filter(self.search_edit.text())

    def show_recent_capture(self, path):
        if self._capture_item is None:
            self._capture_item = QTreeWidgetItem(['点击快捷截图'])
            self._capture_item.setData(0, TYPE_ID_ROLE, '图像点击')
            self._quick_group.addChild(self._capture_item)
        self._capture_item.setText(0, '点击快捷截图')
        self._quick_group.setExpanded(True)
        self._capture_item.setToolTip(0, '拖入表格/流程图即组合为图像点击；范围、偏移和精度可继续编辑。\n'+str(path))
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
            if category_item_.data(0, TYPE_ID_ROLE):
                category_item_.setHidden(not category_match_)
                continue
            any_visible_ = False
            for child_index_ in range(category_item_.childCount()):
                instruction_item_ = category_item_.child(child_index_)
                visible_ = category_match_ or needle_ in instruction_item_.text(0).casefold()
                if instruction_item_ is self._capture_item:
                    visible_ = visible_ or needle_ in instruction_item_.toolTip(0).casefold()
                instruction_item_.setHidden(not visible_)
                any_visible_ = any_visible_ or visible_
            category_item_.setHidden(not any_visible_)
            if any_visible_ and needle_:
                category_item_.setExpanded(True)
