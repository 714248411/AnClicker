"""Searchable, draggable instruction palette."""

from __future__ import annotations

from qt_compat.QtCore import QMimeData, QPoint, Signal, Qt, QStringListModel
from qt_compat.QtGui import QDrag
from qt_compat.QtWidgets import (
    QAbstractItemView,
    QLineEdit,
    QCompleter,
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
        self.search_edit.setPlaceholderText("用中文描述下一步，如：粘贴到表格")
        self.tree = _InstructionTree(self)
        self.tree.setObjectName("instructionTree")

        layout_ = QVBoxLayout(self)
        layout_.setContentsMargins(0, 0, 0, 0)
        layout_.setSpacing(6)
        layout_.addWidget(self.search_edit)
        layout_.addWidget(self.tree, 1)

        self._specs: dict[str, NodeDisplaySpec] = {}
        self._clipboard_ready = False
        self._chosen_suggestion = None
        self._suggestion_model = QStringListModel(self)
        self.completer = QCompleter(self._suggestion_model, self)
        self.completer.setCompletionMode(QCompleter.UnfilteredPopupCompletion)
        self.search_edit.setCompleter(self.completer)
        self.search_edit.textEdited.connect(self._suggest)
        self.completer.activated[str].connect(self._choose_suggestion)
        self.search_edit.textChanged.connect(self._apply_filter)
        self.tree.instructionActivated.connect(self._emit_activation)
        self.tree.itemDoubleClicked.connect(self._quick_action_clicked)
        self.set_specs(specs_ or {})

    def _quick_action_clicked(self, item, column):
        if item is self._quick_capture_item:
            self.clear_quick_actions()
            self.quickCaptureRequested.emit()
        elif item is self._quick_ocr_item:
            self.clear_quick_actions()
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
        self._quick_capture_item.setToolTip(0, '双击截图；完成后在下方拖入“点击快捷截图”，组合成图像点击指令。')
        self._quick_group.addChild(self._quick_capture_item)
        self._quick_ocr_item = QTreeWidgetItem(['快捷截图（OCR）'])
        self._quick_ocr_item.setFlags(self._quick_ocr_item.flags() & ~Qt.ItemFlag.ItemIsDragEnabled)
        self._quick_ocr_item.setToolTip(0, '双击框选范围；完成后在下方选择识字、点击或复制文字。')
        self._quick_group.addChild(self._quick_ocr_item)
        self._guide_item = QTreeWidgetItem(['下一步操作（中文引导）'])
        self._quick_group.addChild(self._guide_item)
        categories_: dict[str, QTreeWidgetItem] = {}
        ocr_shortcuts = ('OCR文字提取', 'OCR复制', 'OCR粘贴', 'OCR点击识别区域')
        for spec_ in self._specs.values():
            # Display groups do not change persisted type IDs or import paths.
            category = ('离线识字OCR' if spec_.category == '本地OCR' else
                        '在线识字OCR' if spec_.type_id == 'OCR识别' else spec_.category)
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
        offline_group = categories_.get('离线识字OCR')
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

    def clear_quick_actions(self):
        for item in (self._quick_capture_item, self._quick_ocr_item, self._guide_item):
            item.takeChildren()
            item.setExpanded(False)
        self._capture_item = None
        self._quick_payload = {}
        self._clipboard_ready = False

    def _show_quick_children(self, parent, actions, payload):
        self.clear_quick_actions()
        self._quick_payload = dict(payload)
        for title, kind in actions:
            item = QTreeWidgetItem([title])
            item.setData(0, TYPE_ID_ROLE, kind)
            item.setToolTip(0, '双击配置并添加，或拖到表格/流程图；自动带入本次快捷操作的设置。\n' + str(payload))
            parent.addChild(item)
            if kind == '图像点击':
                self._capture_item = item
        parent.setExpanded(True)
        self._quick_group.setExpanded(True)
        self._apply_filter(self.search_edit.text())

    def quick_parameters(self, kind):
        if self._chosen_suggestion is not None and self._chosen_suggestion.kind == kind:
            return dict(self._chosen_suggestion.parameters)
        current = self.tree.currentItem()
        if current is not None and current.parent() is self._guide_item and current.data(0, TYPE_ID_ROLE) == kind:
            return dict(current.data(0, TYPE_ID_ROLE + 1) or {})
        if current is not None and current.parent() in (self._quick_capture_item, self._quick_ocr_item):
            if current.data(0, TYPE_ID_ROLE) == kind:
                return dict(getattr(self, '_quick_payload', {}))
        return None

    def show_recent_capture(self, path):
        self._show_quick_children(self._quick_capture_item,
            [('点击快捷截图', '图像点击')], {'图像路径': str(path)})

    def show_recent_ocr(self, region):
        self._show_quick_children(self._quick_ocr_item,
            [('提取识别文字', 'OCR文字提取'), ('点击识别文字', 'OCR点击识别区域'),
             ('复制识别文字', 'OCR复制')], {'区域': str(tuple(region))})

    def _suggest(self, text):
        from instruction_guidance import matching
        self._suggestions = [s for s in matching(text) if s.kind in self._specs]
        self._suggestion_model.setStringList([s.label for s in self._suggestions])
        if text.strip(): self.completer.complete()

    def _choose_suggestion(self, label):
        chosen = next((s for s in getattr(self, '_suggestions', ()) if s.label == label), None)
        if chosen is None: return
        self.search_edit.clear()
        self._chosen_suggestion = chosen
        try: self._emit_activation(chosen.kind)
        finally: self._chosen_suggestion = None

    def command_added(self, kind, parameters=None):
        from instruction_guidance import next_steps
        ready = self._clipboard_ready or kind in ('OCR复制', '复制到剪贴板', '点击并全选复制')
        actions = next_steps(kind, ready)
        self.clear_quick_actions()
        self._clipboard_ready = ready
        self._guide_item.setText(0, ('复制识别文字' if kind == 'OCR复制' else kind) + '后，可以…')
        for action in actions:
            if action.kind not in self._specs: continue
            item = QTreeWidgetItem([action.label])
            item.setData(0, TYPE_ID_ROLE, action.kind)
            item.setData(0, TYPE_ID_ROLE + 1, action.parameters)
            item.setToolTip(0, action.label + '\n双击设置这一步；确认后添加指令，不会立即执行。')
            self._guide_item.addChild(item)
        self._guide_item.setExpanded(True)
        self._quick_group.setExpanded(True)
        self.search_edit.clear()

    def specs(self) -> dict[str, NodeDisplaySpec]:
        return dict(self._specs)

    def selected_type_id(self) -> str | None:
        """Return the selected instruction leaf's type id, if any."""

        return self.tree.instruction_type(self.tree.currentItem())

    def _apply_filter(self, filter_text_) -> None:
        needle = filter_text_.strip().casefold()
        def visit(item, inherited=False):
            match = inherited or needle in (item.text(0) + item.toolTip(0)).casefold()
            child_visible = False
            for i in range(item.childCount()):
                child_visible = visit(item.child(i), match) or child_visible
            visible = match or child_visible
            item.setHidden(not visible)
            if child_visible and needle:
                item.setExpanded(True)
            return visible
        for i in range(self.tree.topLevelItemCount()):
            visit(self.tree.topLevelItem(i))
