"""Searchable, draggable instruction palette."""

from __future__ import annotations

from qt_compat.QtCore import QMimeData, QPoint, Signal, Qt, QStringListModel, QSize
from qt_compat.QtGui import QDrag, QTextDocument, QAbstractTextDocumentLayout, QPalette
from qt_compat.QtWidgets import (
    QAbstractItemView,
    QStyledItemDelegate, QStyleOptionViewItem, QHeaderView, QStyle,
    QLineEdit,
    QMenu,
    QCompleter,
    QTreeWidget,
    QTreeWidgetItem,
    QVBoxLayout,
    QHBoxLayout,
    QWidget,
)

from node_editor.specs import NodeDisplaySpec, normalize_specs


INSTRUCTION_MIME_TYPE = "application/x-clicker-instruction"
TYPE_ID_ROLE = Qt.ItemDataRole.UserRole


class _InstructionSearchEdit(QLineEdit):
    def createStandardContextMenu(self):
        menu = super().createStandardContextMenu()
        translations = {'Undo': '撤销', 'Redo': '重做', 'Cut': '剪切',
                        'Copy': '复制', 'Paste': '粘贴', 'Delete': '删除',
                        'Select All': '全选'}
        for action in menu.actions():
            label, separator, shortcut = action.text().partition('\t')
            translated = translations.get(label.replace('&', '').strip())
            if translated:
                action.setText(translated + (separator + shortcut if separator else ''))
        from context_menu_style import style_context_menu
        style_context_menu(menu, self)
        return menu

    def contextMenuEvent(self, event):
        menu = self.createStandardContextMenu()
        menu.exec(event.globalPos())
        menu.deleteLater()
        event.accept()


class _WrappingInstructionDelegate(QStyledItemDelegate):
    def _document(self, option, index, width):
        styled = QStyleOptionViewItem(option)
        self.initStyleOption(styled, index)
        document = QTextDocument()
        document.setDocumentMargin(0)
        styled.font = self.parent().font()
        document.setDefaultFont(styled.font)
        document.setPlainText(styled.text)
        document.setTextWidth(max(24, width))
        return styled, document

    def sizeHint(self, option, index):
        tree = self.parent()
        depth, ancestor = 1, index.parent()
        while ancestor.isValid():
            depth += 1
            ancestor = ancestor.parent()
        width = max(24, tree.viewport().width() - depth * tree.indentation() - 20)
        styled, document = self._document(option, index, width)
        return QSize(width, int(document.size().height() + max(6, self.parent().fontMetrics().height() * 0.7)))

    def paint(self, painter, option, index):
        styled, document = self._document(option, index, option.rect.width() - 12)
        styled.text = ''
        self.parent().style().drawControl(QStyle.ControlElement.CE_ItemViewItem, styled, painter, self.parent())
        context = QAbstractTextDocumentLayout.PaintContext()
        context.palette = styled.palette
        if styled.state & QStyle.StateFlag.State_Selected:
            context.palette.setColor(QPalette.ColorRole.Text, styled.palette.highlightedText().color())
        painter.save()
        painter.setClipRect(option.rect)
        painter.translate(option.rect.left() + 6, option.rect.top() + max(3, self.parent().fontMetrics().height() * 0.3))
        document.documentLayout().draw(painter, context)
        painter.restore()


class _InstructionTree(QTreeWidget):
    instructionActivated = Signal(str)

    def __init__(self, parent_=None):
        super().__init__(parent_)
        self._drag_start = QPoint()
        self.setHeaderHidden(True)
        self.setWordWrap(True)
        self.setTextElideMode(Qt.TextElideMode.ElideNone)
        self.setUniformRowHeights(False)
        self.setHorizontalScrollBarPolicy(Qt.ScrollBarPolicy.ScrollBarAlwaysOff)
        self.header().setMinimumSectionSize(0)
        self.header().setSectionResizeMode(QHeaderView.ResizeMode.Stretch)
        self.setItemDelegate(_WrappingInstructionDelegate(self))
        self.setIndentation(16)
        self.setDragEnabled(True)
        self.setMouseTracking(True)
        self.setSelectionMode(QAbstractItemView.SelectionMode.SingleSelection)
        self.itemDoubleClicked.connect(self._activate_item)

    def resizeEvent(self, event):
        super().resizeEvent(event)
        self.scheduleDelayedItemsLayout()

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
    scheduleRequested = Signal()
    quickCaptureRequested = Signal()
    quickOcrCaptureRequested = Signal()
    guidanceEnabledChanged = Signal(bool)
    orderChanged = Signal(object)

    def __init__(self, specs_=None, parent_=None):
        super().__init__(parent_)
        self.search_edit = _InstructionSearchEdit(self)
        self.search_edit.setObjectName("instructionSearchEdit")
        self.search_edit.setPlaceholderText("自动展开可进行的下一步操作")
        self.tree = _InstructionTree(self)
        self.tree.setObjectName("instructionTree")

        layout_ = QVBoxLayout(self)
        layout_.setContentsMargins(0, 0, 0, 0)
        layout_.setSpacing(4)
        self.search_row = QWidget(self)
        search_layout = QHBoxLayout(self.search_row)
        search_layout.setContentsMargins(0, 0, 0, 2)
        search_layout.addWidget(self.search_edit, 1, Qt.AlignmentFlag.AlignBottom)
        layout_.addWidget(self.search_row)
        self.tree_surface = QWidget(self)
        self.tree_surface.setObjectName('instructionTreeSurface')
        self.tree_surface.setAttribute(Qt.WidgetAttribute.WA_StyledBackground, True)
        tree_layout = QVBoxLayout(self.tree_surface)
        tree_layout.setContentsMargins(0, 0, 0, 0)
        tree_layout.setSpacing(0)
        tree_layout.addWidget(self.tree, 1)
        layout_.addWidget(self.tree_surface, 1)
        from qt_compat.QtWidgets import QToolButton
        self.schedule_button = QToolButton(self.tree_surface)
        self.schedule_button.setText('⏰')
        self.schedule_button.setObjectName('scheduleTasksButton')
        self.schedule_button.setToolTip('定时运行项目任务')
        self.schedule_button.setAccessibleName('定时任务')
        self.schedule_button.setAutoRaise(True)
        self.schedule_button.setFixedSize(30, 28)
        self.schedule_button.clicked.connect(self.scheduleRequested.emit)
        self.schedule_button.setStyleSheet(
            'QToolButton#scheduleTasksButton {background:transparent; border:none; padding:0;}'
            'QToolButton#scheduleTasksButton:hover {background:rgba(100,120,160,30); border-radius:6px;}')
        # Share the tree's rounded background without covering scrollable entries.
        footer = QHBoxLayout()
        footer.setContentsMargins(4, 0, 4, 4)
        footer.addWidget(self.schedule_button)
        footer.addStretch()
        tree_layout.addLayout(footer)

        self._specs: dict[str, NodeDisplaySpec] = {}
        self.guidance_enabled = True
        self.tree.setContextMenuPolicy(Qt.ContextMenuPolicy.CustomContextMenu)
        self.tree.customContextMenuRequested.connect(self._show_settings_menu)
        self._clipboard_ready = False
        self._chosen_suggestion = None
        self._suggestion_model = QStringListModel(self)
        self.completer = QCompleter(self._suggestion_model, self)
        # Keep a typed Python owner before app-wide styling sees this native popup.
        # Lazily wrapping QCompleter's default view can crash PySide2 after restyling.
        from qt_compat.QtWidgets import QListView
        self._completion_popup = QListView()
        self.completer.setPopup(self._completion_popup)
        self.completer.setCompletionMode(QCompleter.UnfilteredPopupCompletion)
        self.search_edit.setCompleter(self.completer)
        self.search_edit.textEdited.connect(self._suggest)
        self.completer.activated[str].connect(self._choose_suggestion)
        self.search_edit.textChanged.connect(self._apply_filter)
        self.tree.instructionActivated.connect(self._emit_activation)
        self.tree.itemDoubleClicked.connect(self._quick_action_clicked)
        self.set_specs(specs_ or {})

    def _show_settings_menu(self, position):
        item = self.tree.itemAt(position)
        if item is not None:
            self.tree.setCurrentItem(item)
        group = item
        while group is not None and group.parent() is not None:
            group = group.parent()
        # Pin only actual entries, not the generated next-step suggestions.
        pinnable = (item is not None and item.parent() is group
                    and item is not self._guide_item)
        menu = QMenu(self)
        menu.setObjectName('instructionContextMenu')
        from context_menu_style import style_context_menu
        style_context_menu(menu, self)
        settings = menu.addMenu('设置')
        style_context_menu(settings, self)
        guidance = settings.addAction('中文编程提示')
        guidance.setCheckable(True)
        guidance.setChecked(self.guidance_enabled)
        guidance.toggled.connect(self.set_guidance_enabled)
        menu.addSeparator()
        menu.addAction('指令全部展开', self.tree.expandAll)
        menu.addAction('指令取消全部展开', self.tree.collapseAll)
        menu.addSeparator()
        for title, step in (('↑指令栏', -1), ('↓指令栏', 1)):
            action = menu.addAction(title)
            action.setEnabled(self._can_move_group(group, step))
            action.triggered.connect(lambda checked=False, delta=step: self._move_group(group, delta))
        for title, step in (('↑指令', -1), ('↓指令', 1)):
            action = menu.addAction(title)
            action.setEnabled(self._can_move_command(item, step))
            action.triggered.connect(lambda checked=False, delta=step: self._move_command(item, delta))
        menu.addSeparator()
        pin_group = menu.addAction('置顶选中指令栏')
        pin_group.setEnabled(group is not None)
        pin_group.triggered.connect(lambda: self._pin_group(group))
        bottom_group = menu.addAction('置底选中指令栏')
        bottom_group.setEnabled(group is not None)
        bottom_group.triggered.connect(lambda: self._bottom_group(group))
        pin_command = menu.addAction('置顶指令')
        pin_command.setEnabled(pinnable)
        pin_command.triggered.connect(lambda: self._pin_command(item))
        bottom_command = menu.addAction('置底指令')
        bottom_command.setEnabled(pinnable)
        bottom_command.triggered.connect(lambda: self._bottom_command(item))
        try:
            menu.exec(self.tree.viewport().mapToGlobal(position))
        finally:
            menu.deleteLater()

    @staticmethod
    def _order_key(item):
        kind = item.data(0, TYPE_ID_ROLE)
        return 'type:' + str(kind) if kind else 'label:' + item.text(0)

    def _pin_group(self, group):
        if group is None:
            return
        index = self.tree.indexOfTopLevelItem(group)
        if index < 0:
            return
        self.tree.takeTopLevelItem(index)
        self.tree.insertTopLevelItem(0, group)
        group.setExpanded(True)
        self.tree.setCurrentItem(group)
        self.orderChanged.emit(self.instruction_order())

    def _pin_command(self, item):
        if item is None or item.parent() is None or item is self._guide_item:
            return
        parent = item.parent()
        if parent.parent() is not None:
            return
        parent.takeChild(parent.indexOfChild(item))
        parent.insertChild(0, item)
        parent.setExpanded(True)
        self.tree.setCurrentItem(item)
        self.orderChanged.emit(self.instruction_order())

    def _bottom_group(self, group):
        if group is None:
            return
        index = self.tree.indexOfTopLevelItem(group)
        if index < 0:
            return
        self.tree.takeTopLevelItem(index)
        self.tree.addTopLevelItem(group)
        group.setExpanded(True)
        self.tree.setCurrentItem(group)
        self.tree.scrollToItem(group)
        self.orderChanged.emit(self.instruction_order())

    def _bottom_command(self, item):
        if item is None or item.parent() is None or item is self._guide_item:
            return
        parent = item.parent()
        if parent.parent() is not None:
            return
        parent.takeChild(parent.indexOfChild(item))
        # Keep the generated Chinese guidance as the final quick-function row.
        guide_index = parent.indexOfChild(self._guide_item)
        if guide_index >= 0:
            parent.insertChild(guide_index, item)
        else:
            parent.addChild(item)
        parent.setExpanded(True)
        self.tree.setCurrentItem(item)
        self.tree.scrollToItem(item)
        self.orderChanged.emit(self.instruction_order())

    def _can_move_group(self, group, step):
        if group is None:
            return False
        index = self.tree.indexOfTopLevelItem(group)
        return index >= 0 and 0 <= index + step < self.tree.topLevelItemCount()

    def _move_group(self, group, step):
        if not self._can_move_group(group, step):
            return
        index = self.tree.indexOfTopLevelItem(group)
        expanded = group.isExpanded()
        self.tree.takeTopLevelItem(index)
        self.tree.insertTopLevelItem(index + step, group)
        group.setExpanded(expanded)
        self.tree.setCurrentItem(group)
        self.tree.scrollToItem(group)
        self.orderChanged.emit(self.instruction_order())

    def _can_move_command(self, item, step):
        if item is None or item is self._guide_item or item.parent() is None:
            return False
        parent = item.parent()
        if parent.parent() is not None:
            return False
        index = parent.indexOfChild(item)
        target = index + step
        return (index >= 0 and 0 <= target < parent.childCount()
                and parent.child(target) is not self._guide_item)

    def _move_command(self, item, step):
        if not self._can_move_command(item, step):
            return
        parent = item.parent()
        index = parent.indexOfChild(item)
        expanded = item.isExpanded()
        parent.takeChild(index)
        parent.insertChild(index + step, item)
        item.setExpanded(expanded)
        self.tree.setCurrentItem(item)
        self.tree.scrollToItem(item)
        self.orderChanged.emit(self.instruction_order())

    def instruction_order(self):
        groups = [self.tree.topLevelItem(i) for i in range(self.tree.topLevelItemCount())]
        return {
            'groups': [group.text(0) for group in groups],
            'commands': {group.text(0): [self._order_key(group.child(i))
                         for i in range(group.childCount()) if group.child(i) is not self._guide_item]
                         for group in groups},
        }

    def restore_instruction_order(self, order):
        if not isinstance(order, dict):
            return
        groups = order.get('groups', [])
        if isinstance(groups, list):
            position = 0
            for name in dict.fromkeys(name for name in groups if isinstance(name, str)):
                for index in range(position, self.tree.topLevelItemCount()):
                    group = self.tree.topLevelItem(index)
                    if group.text(0) == name:
                        self.tree.takeTopLevelItem(index)
                        self.tree.insertTopLevelItem(position, group)
                        position += 1
                        break
        commands = order.get('commands', {})
        if not isinstance(commands, dict):
            return
        for index in range(self.tree.topLevelItemCount()):
            group = self.tree.topLevelItem(index)
            keys = commands.get(group.text(0), [])
            if not isinstance(keys, list):
                continue
            position = 0
            for key in dict.fromkeys(key for key in keys if isinstance(key, str)):
                for child_index in range(position, group.childCount()):
                    child = group.child(child_index)
                    if child is not self._guide_item and self._order_key(child) == key:
                        group.takeChild(child_index)
                        group.insertChild(position, child)
                        position += 1
                        break

    def set_guidance_enabled(self, enabled):
        enabled = bool(enabled)
        changed = self.guidance_enabled != enabled
        self.guidance_enabled = enabled
        self.tree.setExpandsOnDoubleClick(enabled)
        self._guide_item.setHidden(not enabled)
        if not enabled:
            self._collapse_previous_actions()
            self.completer.popup().hide()
            self._suggestion_model.setStringList([])
            self._suggestions = []
            self._chosen_suggestion = None
        self.search_edit.setPlaceholderText('自动展开可进行的下一步操作' if enabled else '搜索指令')
        self._apply_filter(self.search_edit.text())
        if changed:
            self.guidanceEnabledChanged.emit(enabled)

    def _quick_action_clicked(self, item, column):
        if item is self._quick_capture_item:
            self._collapse_previous_actions()
            self.quickCaptureRequested.emit()
        elif item is self._quick_ocr_item:
            self._collapse_previous_actions()
            self.quickOcrCaptureRequested.emit()

    def _emit_activation(self, type_id_) -> None:
        self.instructionActivated.emit(type_id_)
        self.instructionDoubleClicked.emit(type_id_)

    def set_specs(self, specs_) -> None:
        self._specs = normalize_specs(specs_)
        self._capture_item = None
        self._last_used_branch = None
        self._web_open_item = None
        self._web_category_item = None
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
        if '打开网页' in self._specs:
            self._web_open_item = QTreeWidgetItem(['打开网页'])
            self._web_open_item.setData(0, TYPE_ID_ROLE, '打开网页')
            self._web_open_item.setToolTip(0, '先打开网页，再等待页面或按钮出现，然后点击、输入或获取文字。\n双击加入表格，或拖入表格/流程图；添加后在下方选择下一步，左侧箭头可收起/展开。')
            self._quick_group.addChild(self._web_open_item)
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
            if spec_.type_id == '打开网页':
                self._web_category_item = instruction_item_
                instruction_item_.setToolTip(0, '双击加入表格，再在表格中填写网址；下方显示后续操作，左侧箭头可收起/展开。')
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

    def _collapse_previous_actions(self):
        # Keep children and their parameters for the next use.
        for item in (self._quick_capture_item, self._quick_ocr_item, self._guide_item,
                     self._web_open_item, self._web_category_item):
            if item is not None:
                item.setExpanded(False)
        current = self.tree.currentItem()
        branch = current
        while branch is not None and branch.parent() is not None:
            branch = branch.parent()
        previous = self._last_used_branch
        if previous is not None and previous is not branch:
            previous.setExpanded(False)
        self._last_used_branch = branch

    def clear_quick_actions(self):
        for item in (self._quick_capture_item, self._quick_ocr_item, self._guide_item, self._web_open_item, self._web_category_item):
            if item is None: continue
            item.takeChildren()
            item.setExpanded(False)
        self._capture_item = None
        self._quick_payload = {}
        self._clipboard_ready = False

    def _show_quick_children(self, parent, actions, payload):
        self._collapse_previous_actions()
        parent.takeChildren()
        self._quick_payload = dict(payload)
        for title, kind in actions:
            item = QTreeWidgetItem([title])
            item.setData(0, TYPE_ID_ROLE, kind)
            item.setData(0, TYPE_ID_ROLE + 1, dict(payload))
            item.setToolTip(0, '双击配置并添加，或拖到表格/流程图；自动带入本次快捷操作的设置。\n' + str(payload))
            parent.addChild(item)
            if kind == '图像点击':
                self._capture_item = item
        self._apply_filter(self.search_edit.text())
        self._collapse_previous_actions()
        parent.setExpanded(self.guidance_enabled)
        self._quick_group.setExpanded(True)

    def quick_parameters(self, kind):
        if self._chosen_suggestion is not None and self._chosen_suggestion.kind == kind:
            return dict(self._chosen_suggestion.parameters)
        current = self.tree.currentItem()
        if current is not None and current.parent() in (self._guide_item, self._web_open_item, self._web_category_item) and current.data(0, TYPE_ID_ROLE) == kind:
            return dict(current.data(0, TYPE_ID_ROLE + 1) or {})
        if current is not None and current.parent() in (self._quick_capture_item, self._quick_ocr_item):
            if current.data(0, TYPE_ID_ROLE) == kind:
                return dict(current.data(0, TYPE_ID_ROLE + 1) or {})
        return None

    def show_recent_capture(self, path):
        self._show_quick_children(self._quick_capture_item,
            [('点击快捷截图', '图像点击')], {'图像路径': str(path)})

    def show_recent_ocr(self, region):
        self._show_quick_children(self._quick_ocr_item,
            [('提取识别文字', 'OCR文字提取'), ('点击识别文字', 'OCR点击识别区域'),
             ('复制识别文字', 'OCR复制')], {'区域': str(tuple(region))})

    def _suggest(self, text):
        if not self.guidance_enabled:
            return
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
        if not self.guidance_enabled:
            self._collapse_previous_actions()
            return
        from instruction_guidance import next_steps
        ready = self._clipboard_ready or kind in ('OCR复制', '复制到剪贴板', '点击并全选复制')
        actions = next_steps(kind, ready, parameters)
        from_category = self.tree.currentItem() is self._web_category_item
        self._collapse_previous_actions()
        self._clipboard_ready = ready
        parent = self._guide_item
        if kind == '打开网页':
            parent = (self._web_category_item if from_category else self._web_open_item) or self._guide_item
        parent.takeChildren()
        self._guide_item.setText(0, ('复制识别文字' if kind == 'OCR复制' else kind) + '后，可以…')
        for action in actions:
            if action.kind not in self._specs: continue
            item = QTreeWidgetItem([action.label])
            item.setData(0, TYPE_ID_ROLE, action.kind)
            item.setData(0, TYPE_ID_ROLE + 1, action.parameters)
            item.setToolTip(0, action.label + '\n双击设置这一步；确认后添加指令，不会立即执行。')
            parent.addChild(item)
        parent.setExpanded(True)
        if parent.parent() is not None: parent.parent().setExpanded(True)
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
            if item is self._guide_item and not self.guidance_enabled:
                item.setHidden(True)
                return False
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
