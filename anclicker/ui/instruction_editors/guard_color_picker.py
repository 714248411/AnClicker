"""Single-point health color picker with image-space zoom and pan."""
from anclicker.platform.background_capture import BackgroundCaptureDialog
from anclicker.platform.qt_compat.QtCore import QRect
from anclicker.platform.qt_compat.QtWidgets import QLabel,QPushButton
from .glyph_color_picker import ColorCanvas

class GuardColorPicker(BackgroundCaptureDialog):
    def __init__(self,image,mode='point',parent=None):
        super().__init__(image,'point',parent)
        previous=self.canvas;position=self.layout().indexOf(previous)
        self.layout().removeWidget(previous);previous.deleteLater()
        self.canvas=ColorCanvas(image,self);self.layout().insertWidget(position,self.canvas,1)
        for label in self.findChildren(QLabel):
            if label.text().startswith('单击窗口截图'):
                label.setText('滚轮放大 / 缩小；拖拽平移；左键取色；方向键微调 1 像素，Shift+方向键微调 10 像素。')
            elif label.text().startswith('坐标以原窗口'):
                label.setText('缩放和平移只改变预览，记录的坐标与 RGB 始终来自原始截图。')
        fit=QPushButton('适应窗口');fit.setAutoDefault(False);fit.clicked.connect(self.canvas.fit)
        self.layout().insertWidget(position,fit)
        self.canvas.picked.connect(self._picked)
        self.canvas.deleteRequested.connect(self._clear)
        self.canvas.changed.connect(self._changed)
        self.canvas.viewportChanged.connect(self._changed)
        self._changed()
        available=self.screen().availableGeometry() if self.screen() else None
        if available:self.resize(int(available.width()*.88),int(available.height()*.86))
    def _picked(self,*args):
        x,y=self.canvas.point
        self.canvas.selection=QRect(x,y,1,1)
        self.canvas.markers=[{'point':(x,y)}]
        self.canvas.changed.emit()
    def _clear(self,*args):
        self.canvas.point=None;self.canvas.selection=QRect();self.canvas.markers=[]
        self.canvas.changed.emit();self.canvas.update()
    def _changed(self):
        super()._changed()
        if hasattr(self.canvas,'zoom'):
            scale=self.canvas.image_rect().width()/self.canvas.image.width*100
            self.status.setText(self.status.text()+'；缩放：'+format(scale,'.0f')+'%')
