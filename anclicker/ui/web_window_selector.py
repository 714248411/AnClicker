"""Explicit browser window selection shared by element and anchor editors."""
from anclicker.platform.qt_compat.QtCore import Qt
from anclicker.platform.qt_compat.QtWidgets import QWidget, QHBoxLayout, QComboBox, QPushButton, QMessageBox


class WebWindowSelector(QWidget):
    def __init__(self, list_windows, selected=None, parent=None):
        super().__init__(parent)
        self.list_windows=list_windows
        layout=QHBoxLayout(self);layout.setContentsMargins(0,0,0,0)
        self.combo=QComboBox(self);self.combo.setMinimumWidth(100)
        self.combo.setSizeAdjustPolicy(QComboBox.AdjustToMinimumContentsLengthWithIcon)
        self.combo.setMinimumContentsLength(16)
        self.combo.addItem('当前网页窗口（跟随上一步）',None)
        layout.addWidget(self.combo,1)
        refresh=QPushButton('刷新窗口',self);refresh.clicked.connect(self.refresh);layout.addWidget(refresh)
        self.combo.setToolTip('点击“刷新窗口”列出 AnClicker 已打开的网页窗口，再选择要定位的窗口。')
        self.set_selection(selected)

    def selection(self):
        return self.combo.currentData()

    def set_selection(self, selected):
        if not selected:self.combo.setCurrentIndex(0);return
        for index in range(1,self.combo.count()):
            if self.combo.itemData(index)==selected:self.combo.setCurrentIndex(index);return
        label=str(selected.get('title') or selected.get('url') or selected.get('id'))
        self.combo.addItem(label,selected);self.combo.setCurrentIndex(self.combo.count()-1)
        self.combo.setItemData(self.combo.currentIndex(),str(selected.get('url','')),Qt.ToolTipRole)

    def refresh(self):
        try:
            pages=self.list_windows()
            if pages is None:return
            selected=self.selection()
            self.combo.clear();self.combo.addItem('当前网页窗口（跟随上一步）',None)
            for page in pages:
                label=str(page.get('title') or '未命名网页')+' · '+str(page.get('badge') or page.get('engine') or '')+' · '+str(page.get('id'))+' · '+str(page.get('url',''))
                self.combo.addItem(label,page)
                self.combo.setItemData(self.combo.count()-1,label,Qt.ToolTipRole)
            if selected:
                selected=next((page for page in pages if (selected.get('cdpKey') and page.get('cdpKey')==selected.get('cdpKey')) or (str(page.get('id'))==str(selected.get('id')) and page.get('session')==selected.get('session'))),selected)
            self.set_selection(selected)
            if not pages:self.combo.setToolTip('暂无已打开的网页，请先通过 AnClicker 打开网页，再刷新。')
        except Exception as error:QMessageBox.warning(self,'无法获取网页窗口',str(error))
