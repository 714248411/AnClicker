"""Input-transparent outer shadow for desktops with native shadows disabled."""
import math
from anclicker.platform.qt_compat.QtCore import Qt,QRectF
from anclicker.platform.qt_compat.QtGui import QPainter,QPainterPath,QColor
from anclicker.platform.qt_compat.QtWidgets import QWidget

class WindowShadow(QWidget):
    extent=22
    def __init__(self,owner):
        super().__init__(owner,Qt.Tool|Qt.FramelessWindowHint|Qt.WindowDoesNotAcceptFocus|Qt.WindowTransparentForInput|Qt.NoDropShadowWindowHint)
        self.owner=owner;self.dark=False
        self.setAttribute(Qt.WA_TranslucentBackground)
        self.setAttribute(Qt.WA_TransparentForMouseEvents)
        self.setAttribute(Qt.WA_ShowWithoutActivating)
        self.setFocusPolicy(Qt.NoFocus)

    def sync(self,dark):
        owner=self.owner
        if not owner.isVisible() or owner.isMinimized() or owner.isMaximized() or owner.isFullScreen() or not owner.isWindow():
            self.hide();return
        # Include the native title bar of ordinary settings dialogs.
        bounds=owner.frameGeometry().adjusted(-self.extent,-self.extent,self.extent,self.extent)
        repaint=self.dark!=dark or self.size()!=bounds.size()
        self.dark=dark
        if self.geometry()!=bounds:self.setGeometry(bounds)
        if not self.isVisible():self.show()
        if repaint:self.update()

    def paintEvent(self,event):
        p=QPainter(self);p.setRenderHint(QPainter.Antialiasing)
        inner=QRectF(self.rect()).adjusted(self.extent,self.extent,-self.extent,-self.extent)
        clip=QPainterPath();clip.addRect(QRectF(self.rect()))
        cut=QPainterPath()
        radius=getattr(self.owner,'_window_corner_radius',14 if self.owner.testAttribute(Qt.WA_TranslucentBackground) else 8)
        if self.owner.testAttribute(Qt.WA_TranslucentBackground):cut.addRoundedRect(inner,radius,radius)
        else:cut.addRect(inner)
        p.setClipPath(clip.subtracted(cut))
        p.setPen(Qt.NoPen)
        # Layered Gaussian falloff, drawn only outside the content rectangle.
        peak=55 if self.dark else 34;previous=0
        for spread in range(self.extent,0,-1):
            alpha=peak*math.exp(-spread*spread/105)
            p.setBrush(QColor(0,0,0,max(0,round(alpha-previous))))
            p.drawRoundedRect(inner.adjusted(-spread,-spread+2,spread,spread+2),radius+spread,radius+spread)
            previous=alpha
