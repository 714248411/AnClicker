import sys
from pathlib import Path
sys.path.insert(0,str(Path(__file__).resolve().parents[1]))
from types import SimpleNamespace
from anclicker.platform.qt_compat.QtWidgets import QApplication,QDialog,QVBoxLayout,QComboBox
from anclicker.ui.settings_combo import style_settings_combos
app=QApplication([])
for count in (1,2,3,5,30):
 for pixels in (9,14,22):
  dialog=QDialog();layout=QVBoxLayout(dialog);combo=QComboBox();combo.addItems(['选项 '+str(i) for i in range(count)]);layout.addWidget(combo)
  style_settings_combos(dialog,SimpleNamespace(view_workspace=None))
  dialog.setStyleSheet('QWidget {font-size:'+str(pixels)+'px;}')
  dialog.resize(280,100);dialog.show();app.processEvents()
  combo.showPopup();app.processEvents();app.processEvents()
  view=combo.view();view.scrollToTop();app.processEvents()
  for row in range(min(count,3)):
   rect=view.visualRect(combo.model().index(row,0))
   assert view.viewport().rect().contains(rect), (count,pixels,row,rect,view.viewport().rect())
  combo.hidePopup();dialog.close();dialog.deleteLater();app.processEvents()
print('PASS: 1/2 rows fully visible; 3+ rows show at least 3 across 9/14/22px fonts')
