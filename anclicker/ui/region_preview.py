"""Scaled gray region canvas with draggable edges and corners."""
from anclicker.platform.qt_compat.QtCore import Qt, QRectF, Signal
from anclicker.platform.qt_compat.QtGui import QColor, QPainter, QPen
from anclicker.platform.qt_compat.QtWidgets import QWidget, QSizePolicy, QDialog, QVBoxLayout


class RegionPreview(QWidget):
    region_changed = Signal(object)
    preview_changed = Signal(object, object, str)

    def __init__(self, parent=None):
        super().__init__(parent)
        self.setMinimumHeight(180)
        self.setSizePolicy(QSizePolicy.Expanding, QSizePolicy.Expanding)
        self.setMouseTracking(True)
        self.background_image = None
        self.background_area = None
        self.area = QRectF(0, 0, 1920, 1080)
        self.region = None
        self.drag_edges = ''
        self.message = '请选择并启用区域识别'
        self._fullscreen_dialog = None
        self._is_fullscreen_preview = False
        self.setToolTip('双击全屏预览，Esc 退出全屏')

    def set_region(self, area, region, message=''):
        self.area = QRectF(*area)
        self.region = QRectF(*region) if region else None
        self.message = message
        self.update()
        self.preview_changed.emit(area, region, message)

    def set_background(self, pixmap, area):
        self.background_image = pixmap
        self.background_area = QRectF(*area) if area is not None else None
        self.update()

    def transform(self):
        scale = min(max(1,self.width()-24)/max(1,self.area.width()), max(1,self.height()-42)/max(1,self.area.height()))
        return scale, (self.width()-self.area.width()*scale)/2, 12

    def display_rect(self, rect):
        scale,x,y = self.transform()
        return QRectF(x+(rect.x()-self.area.x())*scale,y+(rect.y()-self.area.y())*scale,rect.width()*scale,rect.height()*scale)

    def paintEvent(self, event):
        painter=QPainter(self)
        painter.fillRect(self.rect(),QColor('#777777'))
        painter.fillRect(self.display_rect(self.area),QColor('#b0b0b0'))
        if self.background_image is not None and self.background_area is not None:
            painter.save()
            painter.setClipRect(self.display_rect(self.area))
            painter.drawPixmap(self.display_rect(self.background_area),self.background_image,QRectF(self.background_image.rect()))
            painter.restore()
        if self.region is not None:
            rect=self.display_rect(self.region)
            painter.fillRect(rect,QColor(35,35,35,120))
            painter.setPen(QPen(QColor('#e53935'),2))
            painter.drawRect(rect)
            painter.setBrush(QColor('#e53935'))
            for x in (rect.left(),rect.center().x(),rect.right()):
                for y in (rect.top(),rect.center().y(),rect.bottom()):
                    if x!=rect.center().x() or y!=rect.center().y():painter.drawRect(QRectF(x-3,y-3,6,6))
        painter.setPen(QColor('white'))
        painter.drawText(QRectF(6,self.height()-26,self.width()-12,24),Qt.AlignCenter,self.message)

    def edges(self, point):
        if self.region is None:return ''
        r=self.display_rect(self.region)
        if not r.adjusted(-7,-7,7,7).contains(point):return ''
        horizontal=min(('l','r'),key=lambda e:abs(point.x()-(r.left() if e=='l' else r.right())))
        if min(abs(point.x()-r.left()),abs(point.x()-r.right()))>min(7,r.width()/3):horizontal=''
        vertical=min(('t','b'),key=lambda e:abs(point.y()-(r.top() if e=='t' else r.bottom())))
        if min(abs(point.y()-r.top()),abs(point.y()-r.bottom()))>min(7,r.height()/3):vertical=''
        return horizontal+vertical or ('move' if r.contains(point) else '')

    def mouseDoubleClickEvent(self, event):
        if event.button() != Qt.LeftButton:
            return super().mouseDoubleClickEvent(event)
        self.drag_edges = ''
        event.accept()
        self.open_fullscreen()

    def open_fullscreen(self):
        if self._is_fullscreen_preview:
            return
        if self._fullscreen_dialog is not None:
            self._fullscreen_dialog.raise_()
            self._fullscreen_dialog.activateWindow()
            return
        dialog = QDialog(self.window())
        dialog.setWindowTitle('区域预览 · Esc 退出全屏')
        dialog.setWindowFlags(Qt.Dialog | Qt.FramelessWindowHint)
        dialog.setWindowModality(Qt.WindowModal)
        layout = QVBoxLayout(dialog)
        layout.setContentsMargins(0,0,0,0)
        canvas = RegionPreview(dialog)
        canvas._is_fullscreen_preview = True
        canvas.background_image = self.background_image
        canvas.background_area = self.background_area
        def values(rect):
            return (rect.x(),rect.y(),rect.width(),rect.height()) if rect is not None else None
        canvas.set_region(values(self.area),values(self.region),self.message + ' · Esc 退出全屏')
        layout.addWidget(canvas)
        def refresh(area,region,message):
            canvas.set_region(area,region,message + ' · Esc 退出全屏')
        self.preview_changed.connect(refresh)
        def changed(region):
            self.region = QRectF(*region)
            self.region_changed.emit(region)
            self.update()
        canvas.region_changed.connect(changed)
        self._fullscreen_dialog = dialog
        def finished(_):
            self.preview_changed.disconnect(refresh)
            self._fullscreen_dialog = None
            dialog.deleteLater()
            self.setFocus()
        dialog.finished.connect(finished)
        if self.screen() is not None:
            dialog.setGeometry(self.screen().geometry())
        dialog.showFullScreen()
        dialog.raise_()
        dialog.activateWindow()

    def mousePressEvent(self,event):
        if event.button()==Qt.LeftButton:
            self.drag_edges=self.edges(event.position())
            self._drag_start = event.position()
            self._drag_region = QRectF(self.region) if self.region is not None else None

    def mouseMoveEvent(self,event):
        edges=self.drag_edges or self.edges(event.position())
        cursors={'l':Qt.SizeHorCursor,'r':Qt.SizeHorCursor,'t':Qt.SizeVerCursor,'b':Qt.SizeVerCursor,'lt':Qt.SizeFDiagCursor,'rb':Qt.SizeFDiagCursor,'lb':Qt.SizeBDiagCursor,'rt':Qt.SizeBDiagCursor,'move':Qt.SizeAllCursor}
        self.setCursor(cursors.get(edges,Qt.ArrowCursor))
        if not self.drag_edges:return
        scale,ox,oy=self.transform()
        x=round((event.position().x()-ox)/scale+self.area.x())
        y=round((event.position().y()-oy)/scale+self.area.y())
        r=QRectF(self.region)
        if edges == 'move':
            original=self._drag_region
            dx=round((event.position().x()-self._drag_start.x())/scale)
            dy=round((event.position().y()-self._drag_start.y())/scale)
            left=max(self.area.left(),min(original.x()+dx,self.area.right()-original.width()))
            top=max(self.area.top(),min(original.y()+dy,self.area.bottom()-original.height()))
            r=QRectF(left,top,original.width(),original.height())
        if 'l' in edges:r.setLeft(max(self.area.left(),min(x,r.right()-1)))
        if 'r' in edges:r.setRight(min(self.area.right(),max(x,r.left()+1)))
        if 't' in edges:r.setTop(max(self.area.top(),min(y,r.bottom()-1)))
        if 'b' in edges:r.setBottom(min(self.area.bottom(),max(y,r.top()+1)))
        self.region=r
        value=tuple(round(v) for v in (r.x(),r.y(),r.width(),r.height()))
        self.region_changed.emit(value)
        self.update()

    def mouseReleaseEvent(self,event):
        self.drag_edges=''
