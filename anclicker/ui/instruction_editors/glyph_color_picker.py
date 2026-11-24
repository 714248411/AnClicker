"""Zoomable frozen-frame picker with ordered color samples."""
from anclicker.platform.qt_compat.QtCore import Qt,QPointF,Signal
from anclicker.platform.qt_compat.QtGui import QPainter,QPen,QColor,QKeySequence
from anclicker.platform.qt_compat.QtWidgets import QShortcut
import copy
from anclicker.platform.qt_compat.QtWidgets import QDialog,QVBoxLayout,QHBoxLayout,QLabel,QPushButton,QLineEdit
from .glyph_capture import GlyphCanvas
from anclicker.platform.vision_tools.glyph_colors import color_name,NAMED_COLORS

class ColorCanvas(GlyphCanvas):
    picked=Signal(object,bool)
    deleteRequested=Signal(int)
    def __init__(self,image,parent=None):
        super().__init__(image,parent);self.mode='point';self.press_pos=None;self.travel=0;self.markers=[]
    def mousePressEvent(self,event):
        self.setFocus();self.press_pos=event.position();self.travel=0
        self.drag=('pan',event.position(),QPointF(self.pan));event.accept()
    def mouseMoveEvent(self,event):
        if self.drag:
            self.travel=max(self.travel,(event.position()-self.press_pos).manhattanLength())
            super().mouseMoveEvent(event)
    def marker_position(self,point):
        r=self.image_rect()
        return QPointF(r.x()+(point[0]+.5)*r.width()/self.image.width,r.y()+(point[1]+.5)*r.height()/self.image.height)
    def mouseReleaseEvent(self,event):
        click=self.press_pos is not None and self.travel<4 and (event.position()-self.press_pos).manhattanLength()<4
        if click and self.drag:
            self.pan=self.drag[2];self.drag=None
            if event.button()==Qt.LeftButton:
                point=self.client_point(event.position())
                if point is not None:self.point=point;self.picked.emit(self.image.getpixel(point),False)
            elif event.button()==Qt.RightButton:
                distances=[((self.marker_position(item['point'])-event.position()).manhattanLength(),i) for i,item in enumerate(self.markers)]
                if distances:
                    distance,index=min(distances)
                    if distance<=20:self.deleteRequested.emit(index)
            self.update()
        else:super().mouseReleaseEvent(event)
        self.press_pos=None;event.accept()
    def paintEvent(self,event):
        super().paintEvent(event)
        painter=QPainter(self)
        for index,item in enumerate(self.markers):
            point=self.marker_position(item['point']);x,y=int(point.x()),int(point.y())
            if not self.rect().adjusted(-15,-15,15,15).contains(x,y):continue
            for color,width in ((QColor('black'),4),(QColor('yellow'),2)):
                painter.setPen(QPen(color,width));painter.drawLine(x-7,y,x+7,y);painter.drawLine(x,y-7,x,y+7)
            text=str(index+1);metrics=painter.fontMetrics();w=metrics.horizontalAdvance(text)+8;h=metrics.height()+4
            bx=max(0,min(self.width()-w,x+8));by=max(0,min(self.height()-h,y-h-5))
            painter.fillRect(bx,by,w,h,QColor('#202020'));painter.setPen(QColor('white'));painter.drawText(bx+4,by+metrics.ascent()+2,text)
    def keyPressEvent(self,event):
        moves={Qt.Key_Left:(-1,0),Qt.Key_Right:(1,0),Qt.Key_Up:(0,-1),Qt.Key_Down:(0,1)}
        if event.key() in moves and self.point is not None:
            dx,dy=moves[event.key()];step=10 if event.modifiers() & Qt.ShiftModifier else 1
            self.point=(max(0,min(self.image.width-1,self.point[0]+dx*step)),max(0,min(self.image.height-1,self.point[1]+dy*step)))
            self.picked.emit(self.image.getpixel(self.point),True);self.update();event.accept();return
        if event.key() in (Qt.Key_Return,Qt.Key_Enter) and self.point is not None:
            self.picked.emit(self.image.getpixel(self.point),False);event.accept();return
        super().keyPressEvent(event)

class GlyphColorPicker(QDialog):
    def __init__(self,image,parent=None,multiple=True,records=None):
        super().__init__(parent);self.setWindowTitle('吸取优先色' if multiple else '吸取文字颜色');self.resize(960,700);self.setMinimumSize(440,360)
        self.multiple=multiple;self.records=records or [];self.samples=[];self.active_sample=None;self.history=[]
        layout=QVBoxLayout(self);hint=QLabel('滚轮缩放；拖拽平移；左键追加取色；右键点击十字删除该点；Ctrl+Z 撤销。方向键微调当前点，角标按创建顺序排列。');hint.setWordWrap(True);layout.addWidget(hint)
        self.canvas=ColorCanvas(image,self);layout.addWidget(self.canvas,1)
        self.status=QLabel('点击文字笔画吸取颜色');self.status.setWordWrap(True);layout.addWidget(self.status)
        self.order=QLineEdit();self.order.setReadOnly(True);self.order.setPlaceholderText('红色;蓝色;黄色;192,40,21');layout.addWidget(self.order)
        row=QHBoxLayout();layout.addLayout(row)
        for text,callback in [('适应窗口',self.canvas.fit),('撤销 Ctrl+Z',self.undo),('清空',self.clear)]:
            button=QPushButton(text);button.setAutoDefault(False);button.clicked.connect(callback);row.addWidget(button)
        row.addStretch();self.use=QPushButton('使用优先顺序' if multiple else '使用颜色');self.use.setAutoDefault(False);self.use.setEnabled(False);self.use.clicked.connect(self.accept);row.addWidget(self.use)
        cancel=QPushButton('取消');cancel.setAutoDefault(False);cancel.clicked.connect(self.reject);row.addWidget(cancel)
        self.canvas.picked.connect(self.add_color);self.canvas.deleteRequested.connect(self.delete_sample)
        self.undoShortcut=QShortcut(QKeySequence('Ctrl+Z'),self);self.undoShortcut.setContext(Qt.WidgetWithChildrenShortcut);self.undoShortcut.activated.connect(self.undo)
        self.canvas.setFocus()
    def remember(self):
        self.history.append((copy.deepcopy(self.samples),self.active_sample))
        if len(self.history)>100:self.history.pop(0)
    def add_color(self,rgb,replace=False):
        self.remember()
        rgb=tuple(map(int,rgb));record=next((r for r in self.records if max(abs(a-b) for a,b in zip(r['rgb'],rgb))<=24),None)
        name=record['color'] if record else color_name(rgb)
        named=record is not None or name in NAMED_COLORS and max(abs(a-b) for a,b in zip(rgb,NAMED_COLORS[name]))<=24
        token=name if named else ','.join(map(str,rgb))
        item={'name':name,'rgb':rgb,'token':token,'point':self.canvas.point}
        if not self.multiple:self.samples=[item];self.active_sample=0
        elif replace and self.active_sample is not None and self.active_sample<len(self.samples):self.samples[self.active_sample]=item
        else:
            self.samples.append(item);self.active_sample=len(self.samples)-1
        self.refresh();point=self.canvas.point
        self.status.setText(f'坐标 {point} · {name} · RGB {rgb}；方向键微调当前取色，点击下一处追加。')
    def refresh(self):
        self.order.setText(';'.join(r['token'] for r in self.samples));self.use.setEnabled(bool(self.samples))
        self.canvas.markers=self.samples
        self.canvas.point=self.samples[self.active_sample]['point'] if self.active_sample is not None and self.active_sample<len(self.samples) else None
        self.canvas.update()
    def delete_sample(self,index):
        if not 0<=index<len(self.samples):return
        self.remember();self.samples.pop(index)
        if self.active_sample is not None:
            if self.active_sample>index:self.active_sample-=1
            elif self.active_sample==index:self.active_sample=min(index,len(self.samples)-1) if self.samples else None
        self.refresh();self.canvas.setFocus()
        self.status.setText('已删除取色点，剩余点按创建顺序重新编号；Ctrl+Z 可恢复。')
    def undo(self):
        if not self.history:return
        self.samples,self.active_sample=self.history.pop()
        self.refresh();self.canvas.setFocus();self.status.setText('已撤销上一步，恢复原有取色顺序。')
    def clear(self):
        if not self.samples:return
        self.remember();self.samples=[];self.active_sample=None;self.refresh();self.canvas.setFocus()
