"""Frozen-image glyph selection, with image-space movement and anchored entry."""
from anclicker.platform.qt_compat.QtCore import Qt,QRect,QRectF,QPointF,Signal
from anclicker.platform.qt_compat.QtWidgets import (QDialog,QVBoxLayout,QHBoxLayout,QLabel,QPushButton,QFrame,QLineEdit,QApplication)
from anclicker.platform.background_capture import CaptureCanvas

class GlyphCanvas(CaptureCanvas):
    enterRequested=Signal()
    viewportChanged=Signal()
    def __init__(self,image,parent=None):
        super().__init__(image,'region',parent)
        self.zoom=1.;self.pan=QPointF();self.drag_image=False;self.space=False;self.drag=None
        self.setFocusPolicy(Qt.StrongFocus)
    def image_rect(self):
        scale=min(max(1,self.width()-20)/self.image.width,max(1,self.height()-20)/self.image.height)*self.zoom
        w,h=self.image.width*scale,self.image.height*scale
        return QRectF((self.width()-w)/2+self.pan.x(),(self.height()-h)/2+self.pan.y(),w,h)
    def fit(self):
        self.zoom=1.;self.pan=QPointF();self.update();self.viewportChanged.emit()
    def zoom_at(self,position,factor):
        old=self.image_rect();new_zoom=max(.1,min(30.,self.zoom*factor));ratio=new_zoom/self.zoom
        left=position.x()-(position.x()-old.x())*ratio;top=position.y()-(position.y()-old.y())*ratio
        self.zoom=new_zoom
        self.pan=QPointF(left-(self.width()-old.width()*ratio)/2,top-(self.height()-old.height()*ratio)/2)
        self.update();self.viewportChanged.emit()
    def wheelEvent(self,event):
        if event.angleDelta().y():self.zoom_at(event.position(),1.2**(event.angleDelta().y()/120))
        event.accept()
    def selection_rect(self):
        r=self.image_rect();s=self.selection
        return QRectF(r.x()+s.x()*r.width()/self.image.width,r.y()+s.y()*r.height()/self.image.height,s.width()*r.width()/self.image.width,s.height()*r.height()/self.image.height)
    def mousePressEvent(self,event):
        self.setFocus();pos=event.position();p=self.client_point(pos)
        if event.button() in (Qt.MiddleButton,Qt.RightButton) or (event.button()==Qt.LeftButton and (self.space or self.drag_image)):
            self.drag=('pan',pos,self.pan);self.setCursor(Qt.ClosedHandCursor)
        elif event.button()==Qt.LeftButton and p is not None:
            if not self.selection.isEmpty() and self.selection.contains(*p):self.drag=('move',p,QRect(self.selection))
            else:
                self.drag=('select',p,None);self.selection=QRect(*p,1,1);self.point=p;self.changed.emit();self.update()
        event.accept()
    def mouseMoveEvent(self,event):
        if not self.drag:return
        mode,start,original=self.drag
        if mode=='pan':
            self.pan=original+event.position()-start;self.viewportChanged.emit()
        else:
            p=self.client_point(event.position(),clamp=True)
            if mode=='move':
                x=max(0,min(self.image.width-original.width(),original.x()+p[0]-start[0]));y=max(0,min(self.image.height-original.height(),original.y()+p[1]-start[1]))
                self.selection=QRect(x,y,original.width(),original.height())
            else:self.selection=QRect(min(start[0],p[0]),min(start[1],p[1]),abs(p[0]-start[0])+1,abs(p[1]-start[1])+1)
            self.point=(self.selection.center().x(),self.selection.center().y());self.changed.emit()
        self.update();event.accept()
    def mouseReleaseEvent(self,event):
        if self.drag:self.mouseMoveEvent(event)
        self.drag=None;self.setCursor(Qt.OpenHandCursor if self.drag_image else Qt.CrossCursor);event.accept()
    def keyPressEvent(self,event):
        key=event.key()
        if key in (Qt.Key_Return,Qt.Key_Enter):self.enterRequested.emit();event.accept();return
        if key==Qt.Key_Space:self.space=True;event.accept();return
        moves={Qt.Key_Left:(-1,0),Qt.Key_Right:(1,0),Qt.Key_Up:(0,-1),Qt.Key_Down:(0,1)}
        if key in moves and not self.selection.isEmpty():
            dx,dy=moves[key];step=10 if event.modifiers() & Qt.ShiftModifier else 1
            x=max(0,min(self.image.width-self.selection.width(),self.selection.x()+dx*step));y=max(0,min(self.image.height-self.selection.height(),self.selection.y()+dy*step))
            self.selection.moveTo(x,y);self.point=(self.selection.center().x(),self.selection.center().y());self.changed.emit();self.update();event.accept();return
        super().keyPressEvent(event)
    def keyReleaseEvent(self,event):
        if event.key()==Qt.Key_Space:self.space=False;event.accept();return
        super().keyReleaseEvent(event)
    def focusOutEvent(self,event):
        self.space=False;super().focusOutEvent(event)
    def resizeEvent(self,event):
        super().resizeEvent(event);self.viewportChanged.emit()

class GlyphCaptureDialog(QDialog):
    def __init__(self,image,text='',parent=None):
        super().__init__(parent);self.setWindowTitle('制作字库 · 框选文字');self.resize(1000,720);self.setMinimumSize(440,360)
        layout=QVBoxLayout(self)
        hint=QLabel('滚轮缩放；左键框选或拖动选框；右键 / 中键 / 空格+左键拖动图片。方向键微调 1 像素，Shift+方向键移动 10 像素；回车输入文字。');hint.setWordWrap(True);layout.addWidget(hint)
        row=QHBoxLayout();layout.addLayout(row)
        self.panButton=QPushButton('拖动图片');self.panButton.setCheckable(True);self.panButton.setAutoDefault(False);row.addWidget(self.panButton)
        fit=QPushButton('适应窗口');fit.setAutoDefault(False);row.addWidget(fit);row.addStretch()
        self.canvas=GlyphCanvas(image,self);layout.addWidget(self.canvas,1)
        self.status=QLabel('请框选一行文字');layout.addWidget(self.status)
        row=QHBoxLayout();layout.addLayout(row);row.addStretch()
        enter=QPushButton('输入文字 ↵');enter.setAutoDefault(False);enter.clicked.connect(self.show_entry);row.addWidget(enter)
        cancel=QPushButton('取消');cancel.setAutoDefault(False);cancel.clicked.connect(self.reject);row.addWidget(cancel)
        self.entryPanel=QFrame(self.canvas);self.entryPanel.setObjectName('glyphTextEntry');self.entryPanel.setAutoFillBackground(True);self.entryPanel.setFrameShape(QFrame.StyledPanel)
        panel=QVBoxLayout(self.entryPanel);panel.setContentsMargins(8,8,8,8);panel.addWidget(QLabel('输入框选文字'))
        self.textEdit=QLineEdit(text);self.textEdit.setPlaceholderText('按从左到右输入文字');panel.addWidget(self.textEdit)
        buttons=QHBoxLayout();panel.addLayout(buttons)
        again=QPushButton('返回调整');again.setAutoDefault(False);again.clicked.connect(self.hide_entry);buttons.addWidget(again)
        confirm=QPushButton('确认文字');confirm.setAutoDefault(False);confirm.clicked.connect(self.confirm_text);buttons.addWidget(confirm)
        self.entryPanel.hide();self.textEdit.returnPressed.connect(self.confirm_text)
        self.canvas.enterRequested.connect(self.show_entry);self.canvas.changed.connect(self.selection_changed);self.canvas.viewportChanged.connect(self.place_entry)
        self.panButton.toggled.connect(self.toggle_pan);fit.clicked.connect(self.canvas.fit)
        self.canvas.setFocus()
    def toggle_pan(self,enabled):
        self.canvas.drag_image=enabled;self.canvas.setCursor(Qt.OpenHandCursor if enabled else Qt.CrossCursor);self.canvas.setFocus()
    def selection_changed(self):
        s=self.canvas.selection;self.status.setText(f'选区：{s.x()},{s.y()} · {s.width()} × {s.height()} 像素；回车输入文字')
        self.place_entry()
    def show_entry(self):
        if self.canvas.selection.isEmpty():return
        self.entryPanel.show();self.place_entry();self.entryPanel.raise_();self.textEdit.setFocus();self.textEdit.selectAll()
    def hide_entry(self):
        self.entryPanel.hide();self.canvas.setFocus()
    def place_entry(self):
        if not hasattr(self,'entryPanel') or not self.entryPanel.isVisible():return
        canvas=self.canvas;bounds=canvas.rect().adjusted(4,4,-4,-4)
        screen=QApplication.screenAt(canvas.mapToGlobal(canvas.rect().center())) or QApplication.primaryScreen()
        if screen:
            area=screen.availableGeometry();bounds=bounds.intersected(QRect(canvas.mapFromGlobal(area.topLeft()),canvas.mapFromGlobal(area.bottomRight())))
        width=max(1,min(330,bounds.width()));self.entryPanel.setFixedWidth(width);self.entryPanel.adjustSize()
        height=self.entryPanel.height();s=canvas.selection_rect()
        x=int(s.left());y=int(s.bottom()+8)
        if y+height>bounds.bottom()+1:y=int(s.top()-height-8)
        x=max(bounds.left(),min(x,bounds.right()-width+1));y=max(bounds.top(),min(y,bounds.bottom()-height+1))
        self.entryPanel.move(x,y)
    def moveEvent(self,event):
        super().moveEvent(event);self.place_entry()
    def confirm_text(self):
        if not self.textEdit.text().strip():self.textEdit.setPlaceholderText('请先输入文字');self.textEdit.setFocus();return
        self.accept()
    def keyPressEvent(self,event):
        if event.key()==Qt.Key_Escape and self.entryPanel.isVisible():self.hide_entry();event.accept();return
        super().keyPressEvent(event)
