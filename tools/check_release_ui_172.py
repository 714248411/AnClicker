import os
os.environ.setdefault('QT_QPA_PLATFORM','offscreen')
import sys
from pathlib import Path
sys.path.insert(0,str(Path(__file__).resolve().parents[1]))
from types import SimpleNamespace
from anclicker.ui.view_workspace import ViewWorkspace
from anclicker.ui.workspace_constants import AGENT_VIEW,TABLE_VIEW
from anclicker.ui.fold_lock_icon import paint_fold_lock
from anclicker.platform.qt_compat.QtWidgets import QApplication
from anclicker.platform.qt_compat.QtGui import QFontInfo,QFont,QImage,QPainter,QPalette,QColor
from anclicker.platform.qt_compat.QtCore import QRectF
app=QApplication.instance() or QApplication([])
host=SimpleNamespace(palette_collapsed=False,_place_palette=lambda:None,refresh_table=lambda:None)
ViewWorkspace._view_changed(host,AGENT_VIEW);assert host.palette_collapsed
ViewWorkspace._view_changed(host,TABLE_VIEW);assert not host.palette_collapsed
widths=[]
for pixels in (8,13,18,30):
 image=QImage(40,40,QImage.Format_ARGB32);image.fill(QColor('white'))
 painter=QPainter(image);font=QFont();font.setPixelSize(pixels)
 palette=QPalette();palette.setColor(QPalette.Base,QColor('white'))
 paint_fold_lock(painter,QRectF(4,4,32,32),False,palette,font);painter.end()
 xs=[x for x in range(40) for y in range(40) if image.pixelColor(x,y).lightness()<200]
 print('font',pixels,QFontInfo(font).pixelSize(),'pixels',len(xs),flush=True)
 widths.append(max(xs)-min(xs)+1 if xs else 0)
assert widths[0]<widths[1]<=widths[2]==widths[3],widths
print('PASS AI default palette collapse, table reopening and bounded font-aware lock rendering',widths)
