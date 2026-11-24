import sys
from pathlib import Path
sys.path.insert(0,str(Path(__file__).resolve().parents[1]))
from anclicker.platform.qt_compat.QtCore import QSize,QRect
from anclicker.ui.instruction_editors.compact_settings import centered_popup_geometry
for available in (QRect(0,0,1920,1040),QRect(-1920,0,1920,1040)):
 for main in (QRect(available.x()+300,200,900,400),QRect(available.x(),0,1180,720)):
  for size in (QSize(500,250),QSize(700,950),QSize(2400,3000)):
   result=centered_popup_geometry(size,main,available)
   assert available.contains(result)
   assert result.height()<=int(main.height()*1.5)
   expected_y=main.center().y()-result.height()//2
   if available.top()<=expected_y<=available.bottom()-result.height()+1: assert result.y()==expected_y
assert centered_popup_geometry(QSize(600,950),QRect(400,300,800,400),QRect(0,0,1920,1080)).height()==600
print('PASS: centering, 1.5x height cap, screen boundaries and negative monitor coordinates')
