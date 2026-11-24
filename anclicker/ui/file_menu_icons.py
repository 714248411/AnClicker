"""Small red outline icons shared by application menus."""
from functools import lru_cache
import math
from anclicker.platform.qt_compat.QtCore import Qt,QRectF,QPointF
from anclicker.platform.qt_compat.QtGui import QIcon,QPixmap,QPainter,QPen,QColor,QPainterPath

@lru_cache(maxsize=48)
def file_menu_icon(kind, stroke_width=1.5):
    icon=QIcon()
    for size in (16,24,32,48):
        pixmap=QPixmap(size,size);pixmap.fill(Qt.transparent)
        painter=QPainter(pixmap);painter.setRenderHint(QPainter.Antialiasing)
        painter.scale(size/20,size/20)
        pen=QPen(QColor('#ef4444'),stroke_width);pen.setCapStyle(Qt.RoundCap);pen.setJoinStyle(Qt.RoundJoin)
        painter.setPen(pen);painter.setBrush(Qt.NoBrush)
        def line(x1,y1,x2,y2):painter.drawLine(QPointF(x1,y1),QPointF(x2,y2))
        def path(points):
            curve=QPainterPath(QPointF(*points[0]))
            for point in points[1:]:curve.lineTo(*point)
            painter.drawPath(curve)
        if kind=='new':
            path([(11,2.5),(4,2.5),(4,17.5),(16,17.5),(16,7.5),(11,2.5),(11,7.5),(16,7.5)])
            line(7,12,13,12);line(10,9,10,15)
        elif kind in ('save','save_as'):
            path([(15,17),(3,17),(3,3),(14,3),(17,6),(17,12 if kind=='save_as' else 17)])
            path([(6,3),(6,8),(13,8),(13,3)])
            if kind=='save':path([(6,17),(6,12),(14,12),(14,17)])
            else:
                path([(10,15),(9,18),(12,17),(18,11),(16,9),(10,15)])
        elif kind=='import':
            path([(3,11),(3,17),(17,17),(17,11)])
            line(10,2.5,10,12);path([(6.5,8.5),(10,12),(13.5,8.5)])
        elif kind=='export':
            path([(3,11),(3,17),(17,17),(17,11)])
            line(10,3,10,12);path([(6.5,6.5),(10,3),(13.5,6.5)])
        elif kind=='clear':
            path([(5,6),(6,17),(14,17),(15,6)])
            line(3,6,17,6);path([(7,6),(7,3),(13,3),(13,6)])
            line(8,9,8.5,14);line(12,9,11.5,14)
        elif kind=='folder':
            path([(2.5,7),(2.5,4),(8,4),(10,6),(17.5,6),(17.5,8)])
            path([(2.5,8),(18,8),(15.5,17),(2.5,17),(2.5,8)])
        elif kind=='settings':
            points=[]
            for i in range(32):
                angle=math.radians(i*11.25)
                radius=8.5 if i%4 in (1,2) else 6.8
                points.append((10+radius*math.cos(angle),10+radius*math.sin(angle)))
            path(points+[points[0]])
            painter.drawEllipse(QRectF(7,7,6,6))
        elif kind=='about':
            painter.drawEllipse(QRectF(3,3,14,14));line(10,9,10,14);line(10,6,10,6.2)
        elif kind=='guide':
            path([(10,5),(7,3.5),(2.5,3.5),(2.5,15.5),(7,15.5),(10,17),(13,15.5),(17.5,15.5),(17.5,3.5),(13,3.5),(10,5),(10,17)])
        elif kind=='keyboard':
            painter.drawRoundedRect(QRectF(2,5,16,11),2,2)
            for y in (8,11):
                for x in (5,8.3,11.6,15):line(x,y,x+.2,y)
            line(6,14,14,14)
        elif kind=='update':
            painter.drawArc(QRectF(3.5,3.5,13,13),35*16,285*16)
            path([(17,3),(17,7),(13,7)])
        elif kind=='recent':
            painter.drawEllipse(QRectF(3,3,14,14));line(10,6,10,10);line(10,10,13,12)
        painter.end();icon.addPixmap(pixmap)
    return icon
