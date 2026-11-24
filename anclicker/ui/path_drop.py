"""Local-file drops for path fields and text composers, without opening files."""
import os
from anclicker.platform.qt_compat.QtCore import QObject, QEvent
from anclicker.platform.qt_compat.QtWidgets import QLineEdit, QPlainTextEdit, QComboBox

PATH_DROP_PROPERTY='anclickerLocalPathDrop'


def handles_path_drop(widget):
    while widget is not None:
        if widget.property(PATH_DROP_PROPERTY):return True
        widget=widget.parentWidget()
    return False


class LocalPathDrop(QObject):
    def __init__(self, control, *, insert=False, multiple=False):
        super().__init__(control)
        self.control=control;self.insert=insert;self.multiple=multiple
        self.surfaces=[control]
        if isinstance(control,QPlainTextEdit):self.surfaces.append(control.viewport())
        if isinstance(control,QComboBox) and control.isEditable():self.surfaces.append(control.lineEdit())
        for surface in self.surfaces:
            surface.setAcceptDrops(True);surface.setProperty(PATH_DROP_PROPERTY,True);surface.installEventFilter(self)

    def eventFilter(self, watched, event):
        if event.type() not in (QEvent.DragEnter,QEvent.DragMove,QEvent.Drop):return False
        mime=event.mimeData()
        if not mime.hasUrls():return False
        urls=mime.urls()
        paths=[os.path.normpath(url.toLocalFile()) for url in urls if url.isLocalFile() and url.toLocalFile()]
        control=self.control
        if len(paths)!=len(urls) or not paths or (len(paths)>1 and not self.multiple) or not control.isEnabled() or (hasattr(control,'isReadOnly') and control.isReadOnly()):
            event.ignore();return True
        if event.type()==QEvent.Drop:
            value='\n'.join(paths)
            if self.insert and isinstance(control,QPlainTextEdit):
                cursor=control.textCursor();cursor.clearSelection();cursor.insertText(value);control.setTextCursor(cursor)
            elif isinstance(control,QPlainTextEdit):control.setPlainText(value)
            elif isinstance(control,QComboBox):control.setEditText(value)
            elif isinstance(control,QLineEdit):control.setText(value)
            control.setFocus()
        event.acceptProposedAction();return True


def enable_path_drop(control, *, insert=False, multiple=False):
    handler=getattr(control,'_local_path_drop',None)
    if handler is None:
        handler=LocalPathDrop(control,insert=insert,multiple=multiple);control._local_path_drop=handler
    return handler
