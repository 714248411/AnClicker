"""Transparent L-shaped corner grips, leaving ordinary edge resizing intact."""
from anclicker.platform.qt_compat.QtCore import Qt,QRect
from anclicker.platform.qt_compat.QtGui import QRegion
from anclicker.platform.qt_compat.QtWidgets import QWidget

class CornerGrip(QWidget):
    reach=22
    edge=8
    def __init__(self,window,right,bottom):
        super().__init__(window)
        self.right=right;self.bottom=bottom;self.drag=None
        self.setObjectName('windowCornerResizeGrip')
        self.setAttribute(Qt.WA_NoSystemBackground)
        self.setAutoFillBackground(False)
        self.setFocusPolicy(Qt.NoFocus)
        self.setCursor(Qt.SizeFDiagCursor if right==bottom else Qt.SizeBDiagCursor)
        self.setToolTip('拖动调整窗口大小')
        n=self.reach;e=self.edge
        self.setMask(QRegion(QRect(n-e if right else 0,0,e,n)).united(QRegion(QRect(0,n-e if bottom else 0,n,e))))

    def paintEvent(self,event):
        pass  # Keep the rounded frame visible; only enlarge its input target.

    def mousePressEvent(self,event):
        if event.button()!=Qt.LeftButton:return
        window=self.parentWidget()
        edges=(Qt.RightEdge if self.right else Qt.LeftEdge)|(Qt.BottomEdge if self.bottom else Qt.TopEdge)
        handle=window.windowHandle()
        if event.spontaneous() and handle is not None and handle.startSystemResize(edges):
            event.accept();return
        self.drag=(event.globalPos(),QRect(window.geometry()))
        event.accept()

    def mouseMoveEvent(self,event):
        if self.drag is None or not event.buttons() & Qt.LeftButton:return
        origin,bounds=self.drag;delta=event.globalPos()-origin;window=self.parentWidget()
        width=max(window.minimumWidth(),min(window.maximumWidth(),bounds.width()+(delta.x() if self.right else -delta.x())))
        height=max(window.minimumHeight(),min(window.maximumHeight(),bounds.height()+(delta.y() if self.bottom else -delta.y())))
        window.setGeometry(bounds.x() if self.right else bounds.right()+1-width,
                           bounds.y() if self.bottom else bounds.bottom()+1-height,width,height)
        event.accept()

    def mouseReleaseEvent(self,event):
        self.drag=None;event.accept()

    def sync(self):
        window=self.parentWidget()
        enabled=(window.isWindow() and window.isVisible() and not window.isMaximized()
            and not window.isFullScreen() and getattr(window,'_isResizeEnabled',True)
            and window.minimumWidth()<window.maximumWidth()
            and window.minimumHeight()<window.maximumHeight())
        if not enabled:self.hide();return
        n=self.reach
        self.setGeometry(window.width()-n if self.right else 0,window.height()-n if self.bottom else 0,n,n)
        self.show();self.raise_()


def register_corner_resize(window):
    grips=getattr(window,'_corner_grips',None)
    if grips is None:
        grips=window._corner_grips=[CornerGrip(window,right,bottom) for right,bottom in ((False,False),(True,False),(False,True),(True,True))]
    for grip in grips:grip.sync()
