import os,sys
from pathlib import Path
sys.path.insert(0,str(Path(__file__).resolve().parents[1]))
os.environ['QT_QPA_PLATFORM']='windows'
from anclicker.platform.qt_compat.QtWidgets import QApplication,QWidget
from anclicker.platform.qt_compat.QtGui import QPainter,QColor
from anclicker.platform.qt_compat.QtCore import Qt
from anclicker.domain.instructions import ExecutionContext
from anclicker.platform.vision_tools.runtime import capture,health_percent
class Sample(QWidget):
    def paintEvent(self,event):
        painter=QPainter(self);painter.fillRect(self.rect(),QColor('white'));painter.fillRect(20,20,50,20,QColor('red'))
app=QApplication([]);window=Sample();window.setWindowTitle('AnClicker capture validation');window.resize(200,100)
window.show();app.processEvents()
from anclicker.platform.qt_compat.QtTest import QTest
QTest.qWait(250)
try:
    image,offset,hwnd=capture({'截图来源':'窗口','窗口句柄':str(int(window.winId())),'窗口标题':window.windowTitle(),'区域':'20,20,100,20'},ExecutionContext())
    assert image.shape==(20,100,3) and offset==(20,20)
    assert health_percent(image,(255,0,0),1)==50
    print('PASS real Windows client capture and relative region: 50 percent red bar')
finally:window.close()
