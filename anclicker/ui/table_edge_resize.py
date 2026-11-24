"""A visible, draggable trailing column edge, even when clipped by the viewport."""
from anclicker.platform.qt_compat.QtCore import Qt,QEvent,QTimer,QRectF
from anclicker.platform.qt_compat.QtGui import QPainter,QPen,QPalette
from anclicker.platform.qt_compat.QtWidgets import QWidget,QApplication,QHeaderView,QStyle

class TableEdgeResizeGrip(QWidget):
    def __init__(self,table):
        self.table=table
        self.header=table.horizontalHeader()
        super().__init__(self.header.viewport())
        self.setCursor(Qt.SplitHCursor)
        self.setToolTip('拖动调整列宽；边界重叠时优先左侧列，双击适应内容')
        self.setMouseTracking(True)
        self.drag=None;self.logical=-1;self.resizing=False
        self.timer=QTimer(self);self.timer.setSingleShot(True);self.timer.timeout.connect(self.sync)
        self.header.viewport().installEventFilter(self)
        self.header.geometriesChanged.connect(self.schedule)
        self.header.sectionResized.connect(self.schedule)
        self.header.sectionMoved.connect(self.schedule)
        self.header.sectionCountChanged.connect(self.schedule)
        table.horizontalScrollBar().valueChanged.connect(self.schedule)
        self.schedule()

    def schedule(self,*_):self.timer.start(0)

    def eventFilter(self,watched,event):
        if event.type() in (QEvent.Resize,QEvent.Show,QEvent.StyleChange,QEvent.PaletteChange):self.schedule()
        return False

    def sync(self):
        h=self.header
        columns=[h.logicalIndex(i) for i in range(h.count()) if not h.isSectionHidden(h.logicalIndex(i))]
        self.logical=columns[-1] if columns else -1
        if self.logical<0:self.hide();return
        left=h.sectionViewportPosition(self.logical)
        right=min(h.viewport().width(),left+h.sectionSize(self.logical))
        grip_right=right
        # The trailing grip must not steal the preceding column's resize edge
        # when only a sliver of the last column remains visible.
        margin=max(4,h.style().pixelMetric(QStyle.PM_HeaderGripMargin,None,h))
        if len(columns)>1 and 0<=left<right and right-left<=8+margin:
            previous=columns[-2]
            if h.sectionResizeMode(previous)==QHeaderView.Interactive:
                self.logical=previous
                left=h.sectionViewportPosition(previous)
                right=min(h.viewport().width(),left+h.sectionSize(previous))
        visible=right>0 and left<right and h.sectionResizeMode(self.logical)==QHeaderView.Interactive
        if not visible:self.hide();return
        self.setGeometry(max(0,grip_right-8),0,8,h.viewport().height())
        self.show();self.raise_();self.update()

    def paintEvent(self,event):
        painter=QPainter(self)
        painter.setRenderHint(QPainter.Antialiasing)
        active=bool(self.underMouse() or self.drag)
        color=self.palette().color(QPalette.Highlight if active else QPalette.Text)
        color.setAlpha(165 if active else 48)
        painter.setPen(Qt.NoPen);painter.setBrush(color)
        height=min(18,max(6,self.height()-14))
        painter.drawRoundedRect(QRectF(3,(self.height()-height)/2,2 if active else 1.2,height),1,1)

    def enterEvent(self,event):self.update();super().enterEvent(event)
    def leaveEvent(self,event):self.update();super().leaveEvent(event)

    def mousePressEvent(self,event):
        if event.button()==Qt.LeftButton and self.logical>=0:
            h=self.header;left=h.sectionViewportPosition(self.logical)
            width=min(h.sectionSize(self.logical),h.viewport().width()-left)
            self.drag=(self.logical,event.globalPos().x(),width)
            self.resizing=False
            event.accept();self.update()
        else:super().mousePressEvent(event)

    def mouseMoveEvent(self,event):
        if self.drag and event.buttons() & Qt.LeftButton:
            logical,start,width=self.drag
            delta=event.globalPos().x()-start
            if self.resizing or abs(delta)>=QApplication.startDragDistance():
                self.resizing=True
                self.header.resizeSection(logical,max(self.header.minimumSectionSize(),width+delta))
                self.sync()
            event.accept()
        else:super().mouseMoveEvent(event)

    def mouseReleaseEvent(self,event):
        if self.drag and event.button()==Qt.LeftButton:
            self.drag=None;self.sync();event.accept()
        else:super().mouseReleaseEvent(event)

    def mouseDoubleClickEvent(self,event):
        if event.button()==Qt.LeftButton and self.logical>=0:
            self.drag=None;self.table.resizeColumnToContents(self.logical);self.sync();event.accept()
        else:super().mouseDoubleClickEvent(event)
