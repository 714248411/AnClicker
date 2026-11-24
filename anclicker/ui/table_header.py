"""Keep a partially visible column label inside the visible header area."""
from anclicker.platform.qt_compat.QtCore import Qt,QRectF
from anclicker.platform.qt_compat.QtGui import QPainterPath,QRegion
from anclicker.platform.qt_compat.QtWidgets import QHeaderView,QStyle,QStyleOptionHeader

class CommandTableHeader(QHeaderView):
    def __init__(self,table):
        super().__init__(Qt.Horizontal,table)
        self.setObjectName("commandTableHeader")
        self.viewport().setObjectName("commandTableHeaderViewport")

    def resizeEvent(self,event):
        super().resizeEvent(event)
        # Clip only the two upper corners; extend the lower arc below the header.
        path=QPainterPath()
        path.addRoundedRect(QRectF(0,0,self.width(),self.height()+8),8,8)
        self.setMask(QRegion(path.toFillPolygon().toPolygon()).intersected(QRegion(self.rect())))

    def paintSection(self,painter,rect,logical):
        visible=rect.intersected(self.viewport().rect())
        if visible==rect or visible.isEmpty():
            return super().paintSection(painter,rect,logical)
        option=QStyleOptionHeader();self.initStyleOption(option)
        option.rect=rect;option.section=logical;option.text=''
        painter.save();painter.setClipRect(visible)
        self.style().drawControl(QStyle.CE_Header,option,painter,self)
        label=str(self.model().headerData(logical,self.orientation(),Qt.DisplayRole) or '')
        option.rect=visible.adjusted(7,0,-7,0)
        option.textAlignment=Qt.AlignCenter
        option.text=self.fontMetrics().elidedText(label,Qt.ElideRight,max(0,option.rect.width()))
        if option.rect.width()>0 and option.text:
            self.style().drawControl(QStyle.CE_HeaderLabel,option,painter,self)
        painter.restore()
