"""Print-style image selection and cancellable batch saving."""
import re
from pathlib import Path
from anclicker.platform.qt_compat.QtCore import QThread, Signal, Qt
from anclicker.platform.qt_compat.QtWidgets import (QDialog,QVBoxLayout,QHBoxLayout,QLabel,
    QRadioButton,QSpinBox,QDialogButtonBox,QMessageBox,QButtonGroup)

class ImageSaveRangeDialog(QDialog):
    def __init__(self, images, parent=None):
        super().__init__(parent)
        self.setWindowTitle('图片另存为 · 保存范围')
        self.resize(440,220)
        self.count=len(images)
        layout=QVBoxLayout(self)
        layout.addWidget(QLabel(f'共 {self.count} 张图片，按抓取结果中的顺序编号。'))
        self.all=QRadioButton('全部图片')
        self.single=QRadioButton('指定图片')
        self.range=QRadioButton('图片范围')
        self.group=QButtonGroup(self)
        for radio in (self.all,self.single,self.range):self.group.addButton(radio)
        layout.addWidget(self.all)
        self.number=QSpinBox();self.first=QSpinBox();self.last=QSpinBox()
        for spin in (self.number,self.first,self.last):spin.setRange(1,max(1,self.count))
        self.last.setValue(max(1,self.count))
        row=QHBoxLayout();row.addWidget(self.single);row.addWidget(QLabel('第'));row.addWidget(self.number);row.addWidget(QLabel('张'));row.addStretch();layout.addLayout(row)
        row=QHBoxLayout();row.addWidget(self.range);row.addWidget(QLabel('从第'));row.addWidget(self.first);row.addWidget(QLabel('张到第'));row.addWidget(self.last);row.addWidget(QLabel('张'));layout.addLayout(row)
        self.preview=QLabel();self.preview.setTextFormat(Qt.PlainText);self.preview.setWordWrap(True);layout.addWidget(self.preview)
        self.images=images
        for radio in (self.all,self.single,self.range):radio.toggled.connect(self.update_controls)
        self.number.valueChanged.connect(self.update_controls)
        self.first.valueChanged.connect(self.update_controls);self.last.valueChanged.connect(self.update_controls)
        buttons=QDialogButtonBox(QDialogButtonBox.Ok|QDialogButtonBox.Cancel)
        buttons.button(QDialogButtonBox.Ok).setText('另存为…');buttons.button(QDialogButtonBox.Cancel).setText('取消')
        buttons.accepted.connect(self.accept);buttons.rejected.connect(self.reject);layout.addWidget(buttons)
        self.all.setChecked(True);self.update_controls()
        from anclicker.ui.settings_theme import apply_settings_theme
        owner=parent
        while owner is not None and not hasattr(owner,'view_workspace'):owner=owner.parentWidget()
        apply_settings_theme(self,owner)

    def update_controls(self,*_):
        self.number.setEnabled(self.single.isChecked())
        self.first.setEnabled(self.range.isChecked());self.last.setEnabled(self.range.isChecked())
        if self.single.isChecked() and self.images:
            item=self.images[self.number.value()-1]
            self.preview.setText(str(item.get('alt') or item.get('name') or item['url'])[:240])
        elif self.range.isChecked():
            self.preview.setText(f'将保存第 {self.first.value()}–{self.last.value()} 张（含首尾）。')
        else:self.preview.setText('全部图片保存到所选文件夹；重名自动递增，不覆盖已有文件。')

    def indices(self):
        if self.single.isChecked():return [self.number.value()-1]
        if self.range.isChecked():
            if self.first.value()>self.last.value():raise ValueError('起始序号不能大于结束序号')
            return list(range(self.first.value()-1,self.last.value()))
        return list(range(self.count))

    def accept(self):
        try:self.indices()
        except ValueError as error:
            QMessageBox.warning(self,'保存范围',str(error));return
        super().accept()

class BatchImageDownloadWorker(QThread):
    progress=Signal(str)
    def __init__(self,parent,images,indices,folder,referer):
        super().__init__(parent)
        self.images,self.indices,self.path,self.referer=images,indices,str(folder),referer
        self.cancelled=False;self.error=None;self.summary='';self.report=[]
    def run(self):
        from anclicker.platform.image_download import download_image
        saved=0;failed=0
        try:
            occupied={value.casefold() for p in Path(self.path).iterdir() for value in (p.name,p.stem)}
            for position,index in enumerate(self.indices,1):
                if self.cancelled:break
                item=self.images[index]
                name=re.sub(r'[<>:"/\\|?*\x00-\x1f]', '_', str(item.get('alt') or item.get('name') or '图片')).strip(' .')[:70] or '图片'
                # Extension is derived from actual image bytes by download_image.
                name=name.replace('.', '_')
                stem=f'{index+1:03d}_{name}'
                target=Path(self.path)/stem;n=1
                while target.name.casefold() in occupied:
                    target=Path(self.path)/(stem+'_'+str(n));n+=1
                occupied.add(target.name.casefold())
                def report_progress(done,total):
                    if not self.cancelled:self.progress.emit(f'正在保存 {position}/{len(self.indices)}（原第 {index+1} 张）'+(f'：{done*100//total}%' if total else ''))
                self.progress.emit(f'正在保存 {position}/{len(self.indices)}（原第 {index+1} 张）…')
                try:
                    result=download_image(item['url'],target,self.referer,lambda:self.cancelled,report_progress)
                    saved+=1;self.report.append(f'第 {index+1} 张：已保存 {result.name}')
                except InterruptedError:break
                except Exception as error:
                    failed+=1;self.report.append(f'第 {index+1} 张：失败 — {error}')
        except Exception as error:
            self.error=str(error)
        remaining=len(self.indices)-saved-failed
        self.summary=('已取消' if self.cancelled else '保存完成')+f'：成功 {saved} 张，失败 {failed} 张，未保存 {remaining} 张。'
        if self.error:self.summary+=' '+self.error
        self.report.insert(0,self.summary+'\n保存文件夹：'+self.path)
