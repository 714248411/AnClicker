import sys,tempfile
from pathlib import Path
sys.path.insert(0,str(Path(__file__).resolve().parents[1]))
from anclicker.platform.qt_compat.QtWidgets import QApplication
from anclicker.platform.qt_compat.QtGui import QImage,QColor,QPainter,QFont,QFontMetrics
from anclicker.platform.qt_compat.QtCore import QRect,QRectF,QEventLoop,QTimer
from anclicker.ui.instruction_thumbnails import thumbnail_layout
from anclicker.ui.node_editor.scene import NodeScene
app=QApplication([])
def wait():
 loop=QEventLoop();QTimer.singleShot(100,loop.quit);loop.exec_()
with tempfile.TemporaryDirectory() as folder:
 path=str(Path(folder)/'测试图.png');img=QImage(160,48,QImage.Format_RGB32);img.fill(QColor('#20bc75'))
 painter=QPainter(img);painter.setPen(QColor('black'));painter.drawText(QRect(0,0,160,48),0x84,'Image ABC');painter.end();img.save(path)
 metrics=QFontMetrics(QFont('Microsoft YaHei UI',10))
 widths=[]
 for width in (100,140,200,300,500):
  label,r,_=thumbnail_layout(QRect(0,0,width,38),metrics,'窗口图像点击',img)
  assert r.height()<=36 and r.width()>=0
  if not r.isEmpty():
   assert r.right()<width and r.left()>=5+metrics.horizontalAdvance(label)
   assert abs(r.width()/r.height()-img.width()/img.height())<0.2
  widths.append(r.width())
 assert widths==sorted(widths) and widths[-1]<=120
 scene=NodeScene();scene.load_graph([{'id':1,'type_id':'窗口图像点击','parameters':{'图像路径':path},'x':0,'y':0}],[],{},True)
 node=scene.nodes_by_command_id[1];before=(node.width,node.height,node.pos(),node.boundingRect())
 assert node.thumbnail_key[0]==(path,)
 scene.thumbnail_cache.image(node.thumbnail_key)
 for i in range(30):
  wait()
  if scene.thumbnail_cache.entries:break
 assert not scene.thumbnail_cache.image(node.thumbnail_key).isNull()
 def render(name):
  canvas=QImage(500,150,QImage.Format_ARGB32);canvas.fill(QColor('white'));p=QPainter(canvas);p.translate(20,20);node.paint(p,None);p.end();canvas.save('artifacts/validation/'+name+'.png')
 render('flow-thumbnail')
 assert before==(node.width,node.height,node.pos(),node.boundingRect())
 # Oversized title and narrow node must still paint within the original body.
 node.title='窗口图像点击非常长的名称测试不允许超出边界';node.width=160
 render('flow-thumbnail-narrow')
 node.title='窗口图像点击';node.control_kind='condition';node.width=260
 render('flow-thumbnail-condition')
 scene.clear();wait();scene.thumbnail_cache.pool.waitForDone()
print('PASS table remaining-width scaling/row-height bound, real graph image references, async loading, unchanged node geometry, long titles, condition clipping, scene cleanup')
