"""Local model management UI; copies and unloads run outside the UI thread."""
from anclicker.platform.qt_compat.QtCore import QThread,Signal,Qt
from anclicker.platform.qt_compat.QtWidgets import QVBoxLayout,QHBoxLayout,QLabel,QListWidget,QListWidgetItem,QPushButton,QFileDialog,QMessageBox
from models.model_library import ModelLibrary
from anclicker.ui.information_dialogs import InformationDialog, information_theme, apply_information_theme

class LibraryWorker(QThread):
    result=Signal(object)
    def __init__(self,library,action,value,parent):
        super().__init__(parent);self.library=library;self.action=action;self.value=value
    def run(self):
        try:self.result.emit(self.library.apply(self.action,self.value))
        except Exception as error:self.result.emit({'error':str(error)})

class LocalModelDialog(InformationDialog):
    def __init__(self,parent,library=None):
        super().__init__(parent);self.library=library or ModelLibrary();self.worker=None;self.activate=False;self.changed=False
        self.setWindowTitle('本地模型管理');self.resize(700,440)
        colors=information_theme(parent)
        apply_information_theme(self,colors)
        self.setStyleSheet(self.styleSheet()+f"QListWidget {{background:{colors['surface']};color:{colors['text']};border:1px solid {colors['line']};border-radius:7px;padding:6px;}} QListWidget::item {{padding:10px;}} QListWidget::item:selected {{background:{colors['accent']};color:{colors['accent_text']};}} QPushButton:disabled {{color:{colors['dim']};}}")
        layout=QVBoxLayout(self)
        hint=QLabel('选择 GGUF 模型并切换。添加时复制到 models 目录；删除的文件保留在 models/.trash。');hint.setWordWrap(True);layout.addWidget(hint)
        self.dual_button=QPushButton('启用推荐双模型 · 拆句 + 指令/编辑');layout.addWidget(self.dual_button);self.dual_button.clicked.connect(lambda:self.run_action('dual',True))
        self.dual_button.setToolTip('优先使用通过验收的推荐版本；列表中的切换按钮恢复单模型')
        self.items=QListWidget();layout.addWidget(self.items,1)
        self.status=QLabel();self.status.setWordWrap(True);layout.addWidget(self.status)
        bar=QHBoxLayout();layout.addLayout(bar)
        self.add=QPushButton('新增模型');self.select=QPushButton('切换并启动');self.delete=QPushButton('删除模型');self.close_button=QPushButton('关闭')
        for b in (self.add,self.select,self.delete,self.close_button):bar.addWidget(b)
        self.add.clicked.connect(self.add_model);self.select.clicked.connect(lambda:self.run_action('select'));self.delete.clicked.connect(self.delete_model);self.close_button.clicked.connect(self.accept)
        self.items.itemSelectionChanged.connect(self.buttons);self.reload()
    def reload(self):
        self.items.clear()
        for row in self.library.list():
            item=QListWidgetItem(('当前 · ' if row['active'] else '')+row['file']+'  ('+str(round(row['bytes']/1024**3,2))+' GB)')
            item.setData(Qt.UserRole,row['file']);self.items.addItem(item)
            if row['active']:self.items.setCurrentItem(item)
        if self.items.currentRow()<0 and self.items.count():self.items.setCurrentRow(0)
        current=self.library.dual_config()
        description=('；当前双模型：'+str(current.get('splitter'))+' + '+str(current.get('converter'))) if current.get('enabled') else ''
        self.status.setText('共 '+str(self.items.count())+' 个本地模型'+description);self.buttons()
    def buttons(self):
        idle=self.worker is None;item=self.items.currentItem()
        candidate=self.library.recommended_dual()
        self.dual_button.setEnabled(idle and candidate is not None)
        self.dual_button.setToolTip(('将使用：'+candidate['splitter']+' + '+candidate['converter']) if candidate else '没有可用的双模型')
        self.add.setEnabled(idle);self.close_button.setEnabled(idle);self.items.setEnabled(idle)
        self.select.setEnabled(idle and item is not None)
        self.delete.setEnabled(idle and item is not None and item.data(Qt.UserRole)!=self.library.active())
        self.delete.setToolTip('当前模型请先切换后再删除')
    def add_model(self):
        path,_=QFileDialog.getOpenFileName(self,'添加本地模型','','GGUF 模型 (*.gguf)')
        if path:self.run_action('add',path)
    def delete_model(self):
        item=self.items.currentItem()
        if item and QMessageBox.question(self,'删除本地模型','删除 '+item.data(Qt.UserRole)+'？文件将移到 models/.trash，可手动恢复。',QMessageBox.Yes|QMessageBox.No,QMessageBox.No)==QMessageBox.Yes:self.run_action('delete')
    def run_action(self,action,value=None):
        if self.worker:return
        item=self.items.currentItem()
        if value is None:
            if not item:return
            value=item.data(Qt.UserRole)
        self.worker=LibraryWorker(self.library,action,value,self);self.result=None
        self.worker.result.connect(self.received);self.worker.finished.connect(self.completed)
        self.status.setText('正在处理，请稍候…');self.buttons();self.worker.start()
    def received(self,result):self.result=result
    def completed(self):
        worker=self.worker;worker.wait();self.worker=None;worker.deleteLater()
        result=self.result or {'error':'操作未返回结果'};self.reload()
        if 'error' in result:QMessageBox.warning(self,'模型操作失败',result['error']);return
        self.changed=True;self.status.setText(result['message'])
        if result.get('activate'):self.activate=True;self.accept()
    def reject(self):
        if self.worker is None:super().reject()
    def closeEvent(self,event):
        if self.worker:event.ignore()
        else:super().closeEvent(event)
