"""Chinese command completion that preserves IME composition and existing code."""
from qt_compat.QtCore import Qt, QStringListModel, QTimer
from qt_compat.QtGui import QTextCursor, QKeySequence
from qt_compat.QtWidgets import QPlainTextEdit, QCompleter, QMenu
from instruction_guidance import matching, next_steps, command_template, Suggestion

class GuidedCodeEditor(QPlainTextEdit):
    def __init__(self, parent=None):
        super().__init__(parent)
        self.guidance_enabled=True
        self._composing=False
        self._choices=[]
        self._model=QStringListModel(self)
        self.completer=QCompleter(self._model,self)
        # Keep a typed Python owner before app-wide styling sees this native popup.
        # Lazily wrapping QCompleter's default view can crash PySide2 after restyling.
        from qt_compat.QtWidgets import QListView
        self._completion_popup = QListView()
        self.completer.setPopup(self._completion_popup)
        self.completer.setWidget(self)
        self.completer.setCompletionMode(QCompleter.UnfilteredPopupCompletion)
        self.completer.activated[str].connect(self._accept)
        self.setPlaceholderText('输入中文动作，如“复制文字”“粘贴到网页”；↑↓选择，Tab/回车插入，Esc关闭。Ctrl+空格查看候选。')
        self.cursorPositionChanged.connect(self._cursor_changed)

    def contextMenuEvent(self, event):
        from context_menu_style import style_context_menu
        self.completer.popup().hide()
        menu = QMenu(self)
        style_context_menu(menu, self)
        editable = not self.isReadOnly()
        selected = self.textCursor().hasSelection()

        def add(label, callback, enabled, shortcut=None):
            action = menu.addAction(label, callback)
            action.setEnabled(enabled)
            if shortcut is not None:
                action.setShortcut(QKeySequence(shortcut))
            return action

        add('撤销', self.undo, editable and self.document().isUndoAvailable(), QKeySequence.StandardKey.Undo)
        add('重做', self.redo, editable and self.document().isRedoAvailable(), QKeySequence.StandardKey.Redo)
        menu.addSeparator()
        add('剪切', self.cut, editable and selected, QKeySequence.StandardKey.Cut)
        add('复制', self.copy, selected, QKeySequence.StandardKey.Copy)
        add('粘贴', self.paste, editable and self.canPaste(), QKeySequence.StandardKey.Paste)
        add('删除选中文字', self._delete_selected_text, editable and selected)
        menu.addSeparator()
        add('全选', self.selectAll, not self.document().isEmpty(), QKeySequence.StandardKey.SelectAll)
        try:
            menu.exec(event.globalPos())
        finally:
            menu.deleteLater()
        event.accept()

    def _delete_selected_text(self):
        if self.isReadOnly():
            return
        cursor = self.textCursor()
        if cursor.hasSelection():
            cursor.removeSelectedText()
            self.setTextCursor(cursor)

    def set_guidance_enabled(self, enabled):
        self.guidance_enabled = bool(enabled)
        if not enabled:
            self.completer.popup().hide()
            self._choices = []
        self.setPlaceholderText('输入中文动作，选择提示插入指令；Ctrl+空格查看候选。' if enabled else '在此编辑流程代码')

    def _cursor_changed(self):
        self.completer.popup().hide()

    def inputMethodEvent(self,event):
        self._composing=bool(event.preeditString())
        if self._composing:self.completer.popup().hide()
        super().inputMethodEvent(event)
        if not self._composing and event.commitString():QTimer.singleShot(0,self.show_suggestions)

    def keyPressEvent(self,event):
        popup=self.completer.popup()
        if popup.isVisible() and not self._composing:
            if event.key() in (Qt.Key_Return,Qt.Key_Enter,Qt.Key_Tab):
                index=popup.currentIndex()
                if not index.isValid():index=self._model.index(0,0)
                self._accept(index.data());event.accept();return
            if event.key()==Qt.Key_Escape:
                popup.hide();event.accept();return
        if event.key()==Qt.Key_Space and event.modifiers() & Qt.ControlModifier:
            self.show_suggestions(force=True);event.accept();return
        super().keyPressEvent(event)
        if not self._composing and (event.text() or event.key()==Qt.Key_Backspace):
            self.show_suggestions()

    def show_suggestions(self,force=False):
        if self._composing or not self.guidance_enabled:return
        cursor=self.textCursor()
        line=cursor.block().text()
        prefix=line[:cursor.positionInBlock()]
        if '(' in prefix or prefix.lstrip().startswith('#') or cursor.hasSelection():
            self.completer.popup().hide();return
        self._prefix=prefix
        self._block_position=cursor.block().position()
        if prefix.strip():
            self._choices=matching(prefix)
        else:
            previous=cursor.block().previous().text().strip().split('(',1)[0]
            preceding=self.toPlainText()[:cursor.block().position()]
            ready=any(k+'(' in preceding for k in ('OCR复制','复制到剪贴板','点击并全选复制'))
            self._choices=list(next_steps(previous,ready))
            if not self._choices and force:self._choices=matching('')
        self._model.setStringList([s.label for s in self._choices])
        if not self._choices:self.completer.popup().hide();return
        rect=self.cursorRect();rect.setWidth(max(340,self.completer.popup().sizeHintForColumn(0)+30))
        self.completer.complete(rect)
        self.completer.popup().setCurrentIndex(self._model.index(0,0))

    def _accept(self,label):
        if not self.guidance_enabled:return
        choice=next((s for s in self._choices if s.label==label),None)
        if choice is None:return
        cursor=self.textCursor()
        if cursor.block().position()!=self._block_position:return
        prefix=cursor.block().text()[:cursor.positionInBlock()]
        if prefix!=self._prefix:return
        template=command_template(choice)
        indent=prefix[:len(prefix)-len(prefix.lstrip())]
        cursor.beginEditBlock()
        cursor.setPosition(self._block_position)
        cursor.setPosition(self._block_position+len(prefix),QTextCursor.KeepAnchor)
        cursor.insertText(indent+template)
        cursor.endEditBlock()
        self.setTextCursor(cursor)
        self.completer.popup().hide()
        self.setFocus()

    def insert_command(self,kind):
        self.insertPlainText(command_template(Suggestion(kind,kind))+'\n')
        self.setFocus()
