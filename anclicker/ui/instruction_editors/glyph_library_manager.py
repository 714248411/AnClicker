"""Qt sample browser for the extracted ffly glyph library."""
from pathlib import Path
from anclicker.platform.qt_compat.QtCore import Qt,QSize
from anclicker.platform.qt_compat.QtGui import QIcon,QPixmap
from anclicker.platform.qt_compat.QtWidgets import (QDialog,QVBoxLayout,QHBoxLayout,QSplitter,QWidget,QListWidget,QListWidgetItem,QAbstractItemView,QPushButton,QLabel,QCheckBox,QInputDialog,QMessageBox,QComboBox)
from anclicker.platform.vision_tools.glyphs import GlyphLibrary

class GlyphLibraryManager(QDialog):
    def __init__(self,directory,parent=None):
        super().__init__(parent)
        self.library=GlyphLibrary(str(directory));self.setWindowTitle('字库查看与管理');self.resize(850,560)
        layout=QVBoxLayout(self)
        self.info=QLabel();self.info.setWordWrap(True);layout.addWidget(self.info)
        strict=QCheckBox('按字库优先顺序识别（关闭后选择相似度最高的样本）');strict.setChecked(self.library.strict)
        strict.toggled.connect(self.library.set_strict);layout.addWidget(strict)
        self.colorVersions=QComboBox();self.colorVersions.setToolTip('本名匹配各颜色；带尾号名称仅匹配对应颜色。可在字库点击中选择优先色。');layout.addWidget(self.colorVersions)
        splitter=QSplitter();layout.addWidget(splitter,1)
        self.labels=QListWidget();self.samples=QListWidget()
        self.samples.setViewMode(QListWidget.IconMode);self.samples.setIconSize(QSize(96,96));self.samples.setGridSize(QSize(130,140));self.samples.setResizeMode(QListWidget.Adjust)
        for listing in (self.labels,self.samples):
            listing.setDragDropMode(QAbstractItemView.InternalMove);listing.setDefaultDropAction(Qt.MoveAction)
        for listing,buttons in ((self.labels,[('上移',lambda:self.move_label(-1)),('下移',lambda:self.move_label(1)),('更名',self.rename),('删除文字',self.delete_label)]),(self.samples,[('上移',lambda:self.move_sample(-1)),('下移',lambda:self.move_sample(1)),('删除样本',self.delete_sample)])):
            pane=QWidget();column=QVBoxLayout(pane);column.setContentsMargins(0,0,0,0);column.addWidget(listing)
            row=QHBoxLayout();column.addLayout(row)
            for text,callback in buttons:
                button=QPushButton(text);button.clicked.connect(lambda checked=False,cb=callback:self.guarded(cb));row.addWidget(button)
            splitter.addWidget(pane)
        splitter.setSizes([230,600])
        self.labels.currentTextChanged.connect(self.refresh_samples)
        self.labels.model().rowsMoved.connect(self.save_label_order)
        self.samples.model().rowsMoved.connect(self.save_sample_order)
        footer=QHBoxLayout();layout.addLayout(footer)
        clear=QPushButton('清空字库');clear.clicked.connect(lambda:self.guarded(self.clear));footer.addWidget(clear);footer.addStretch()
        close=QPushButton('关闭');close.clicked.connect(self.accept);footer.addWidget(close)
        from anclicker.ui.settings_theme import apply_settings_theme
        apply_settings_theme(self,parent);self.refresh()
    def guarded(self,callback):
        try:callback()
        except Exception as error:QMessageBox.warning(self,'字库操作未完成',str(error))
    def current(self):
        item=self.labels.currentItem();return item.text() if item else ''
    def refresh(self,selected=None):
        from anclicker.platform.vision_tools.glyph_colors import load_variants
        records=load_variants(self.library.dir);self.colorVersions.clear()
        self.colorVersions.addItems([r['alias']+'（'+r['color']+' · '+','.join(map(str,r['rgb']))+'）' for r in records] or ['尚未录入颜色版本'])
        selected=selected or self.current();self.labels.clear();self.labels.addItems(self.library.labels())
        matches=self.labels.findItems(selected,Qt.MatchExactly)
        if matches:self.labels.setCurrentItem(matches[0])
        elif self.labels.count():self.labels.setCurrentRow(0)
        else:self.samples.clear()
        self.info.setText(f'{self.library.dir}\n共 {len(self.library.labels())} 个字，{len(self.library)} 个样本。可拖动文字及样本调整优先顺序。')
    def refresh_samples(self,*args):
        self.samples.clear();label=self.current()
        for index,name in enumerate(self.library.samples(label)):
            item=QListWidgetItem(QIcon(QPixmap(self.library.sample_path(label,name)).scaled(96,96,Qt.KeepAspectRatio,Qt.FastTransformation)),f'样本 {index+1}')
            item.setData(Qt.UserRole,name);item.setToolTip(name);self.samples.addItem(item)
    def save_label_order(self,*args):
        self.library.reorder_labels([self.labels.item(i).text() for i in range(self.labels.count())])
    def save_sample_order(self,*args):
        self.library.reorder_samples(self.current(),[self.samples.item(i).data(Qt.UserRole) for i in range(self.samples.count())])
    def move_label(self,delta):
        label=self.current();self.library.move_label(label,delta);self.refresh(label)
    def move_sample(self,delta):
        row=self.samples.currentRow()
        if row<0:return
        self.library.move_sample(self.current(),row,delta);self.refresh_samples();self.samples.setCurrentRow(max(0,min(self.samples.count()-1,row+delta)))
    def invalidate_phrases(self):
        # Exact phrase caches must never bypass renamed/deleted character samples.
        from anclicker.platform.vision_tools.glyph_colors import load_variants
        records=load_variants(self.library.dir)
        if records:
            records=[r for r in records if all(c in self.library.index for c in r['text'])]
            GlyphLibrary._atomic_json(str(Path(self.library.dir)/'colors.json'),records)
        directory=Path(self.library.dir)/'phrases'
        if directory.is_dir():
            for path in directory.glob('*.png'):path.unlink()
    def rename(self):
        label=self.current()
        if not label:return
        new,ok=QInputDialog.getText(self,'更名','文字（不能与现有名称重复）',text=label)
        if ok and new.strip()!=label:
            if not self.library.rename_label(label,new):raise ValueError('名称为空或已存在')
            self.invalidate_phrases();self.refresh(new.strip())
    def confirmed(self,text):
        return QMessageBox.question(self,'确认删除',text,QMessageBox.Yes|QMessageBox.No,QMessageBox.No)==QMessageBox.Yes
    def delete_label(self):
        label=self.current()
        if label and self.confirmed('删除文字“'+label+'”及其全部样本？'):
            self.library.remove_label(label);self.invalidate_phrases();self.refresh()
    def delete_sample(self):
        row=self.samples.currentRow();label=self.current()
        if row>=0 and self.confirmed('删除当前样本？'):
            self.library.remove_sample(label,row);self.invalidate_phrases();self.refresh(label)
    def clear(self):
        if self.confirmed('清空当前字库的所有文字及样本？'):
            for label in list(self.library.labels()):self.library.remove_label(label)
            self.invalidate_phrases();self.refresh()
