"""Chinese command completion that preserves IME composition and existing code."""
from qt_compat.QtCore import Qt, QStringListModel, QTimer
from qt_compat.QtGui import QTextCursor
from qt_compat.QtWidgets import QPlainTextEdit, QCompleter
from instruction_guidance import matching, next_steps, command_template, Suggestion

class GuidedCodeEditor(QPlainTextEdit):
    def __init__(self, parent=None):
        super().__init__(parent)
        self._composing=False
        self._choices=[]
        self._model=QStringListModel(self)
        self.completer=QCompleter(self._model,self)
        self.completer.setWidget(self)
        self.completer.setCompletionMode(QCompleter.UnfilteredPopupCompletion)
        self.completer.activated[str].connect(self._accept)
        self.setPlaceholderText('输入中文动作，如“复制文字”“粘贴到网页”；↑↓选择，Tab/回车插入，Esc关闭。Ctrl+空格查看候选。')
        self.cursorPositionChanged.connect(self._cursor_changed)

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
        if self._composing:return
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
