"""Editable per-instruction color priorities; changes do not rewrite shared libraries."""
import json
from anclicker.platform.qt_compat.QtCore import Qt
from anclicker.platform.qt_compat.QtWidgets import (QDialog,QVBoxLayout,QHBoxLayout,QLabel,QTableWidget,QTableWidgetItem,QAbstractItemView,QHeaderView,QPushButton,QDialogButtonBox,QMenu,QMessageBox)
from anclicker.platform.vision_tools.glyph_colors import priority_tokens,rgb_value,NAMED_COLORS

class GlyphPriorityTable(QDialog):
    def __init__(self,current,records,config='[]',tolerance=45,parent=None):
        super().__init__(parent);self.setWindowTitle('选择优先色');self.resize(720,460);self.value='';self.config='[]'
        layout=QVBoxLayout(self);hint=QLabel('勾选需要的颜色，按表格从上到下匹配。右键可上移、下移或修改名称、RGB 色值及容差；双击单元格也可编辑。');hint.setWordWrap(True);layout.addWidget(hint)
        self.table=QTableWidget(0,4);self.table.setHorizontalHeaderLabels(['启用','颜色名称','RGB 色值','容差']);self.table.setSelectionBehavior(QAbstractItemView.SelectRows);self.table.setSelectionMode(QAbstractItemView.SingleSelection)
        self.table.horizontalHeader().setSectionResizeMode(0,QHeaderView.ResizeToContents);self.table.horizontalHeader().setSectionResizeMode(1,QHeaderView.Stretch);self.table.horizontalHeader().setSectionResizeMode(2,QHeaderView.Stretch);self.table.horizontalHeader().setSectionResizeMode(3,QHeaderView.ResizeToContents)
        self.table.setContextMenuPolicy(Qt.CustomContextMenu);self.table.customContextMenuRequested.connect(self.menu);layout.addWidget(self.table)
        try:saved=json.loads(config or '[]')
        except (ValueError,TypeError):saved=[]
        if not isinstance(saved,list):saved=[]
        candidates=[r for r in saved if isinstance(r,dict) and 'name' in r and 'rgb' in r]
        candidates += [{'name':r['color'],'rgb':r['rgb'],'tolerance':tolerance} for r in records]
        selected=priority_tokens(current);used=set()
        for token in selected:
            found=next((r for r in candidates if r['name']==token),None)
            if found is None:
                try:rgb=rgb_value(token)
                except ValueError:rgb=NAMED_COLORS.get(token)
                found={'name':token,'rgb':rgb or '', 'tolerance':tolerance}
            self.add_row(found,True);used.add(found['name'])
        for row in candidates:
            if row['name'] not in used:self.add_row(row,False);used.add(row['name'])
        row=QHBoxLayout();layout.addLayout(row)
        add=QPushButton('新增颜色');add.clicked.connect(lambda:self.add_row({'name':'新颜色','rgb':(255,0,0),'tolerance':tolerance},True));row.addWidget(add)
        delete=QPushButton('删除选中');delete.clicked.connect(self.delete_row);row.addWidget(delete);row.addStretch()
        buttons=QDialogButtonBox(QDialogButtonBox.Ok|QDialogButtonBox.Cancel);buttons.button(QDialogButtonBox.Ok).setText('确定');buttons.button(QDialogButtonBox.Cancel).setText('取消');buttons.accepted.connect(self.accept);buttons.rejected.connect(self.reject);row.addWidget(buttons)
    def add_row(self,data,enabled):
        row=self.table.rowCount();self.table.insertRow(row)
        item=QTableWidgetItem();item.setFlags(Qt.ItemIsEnabled|Qt.ItemIsSelectable|Qt.ItemIsUserCheckable);item.setCheckState(Qt.Checked if enabled else Qt.Unchecked);self.table.setItem(row,0,item)
        rgb=data['rgb'];rgb=','.join(map(str,rgb)) if isinstance(rgb,(tuple,list)) else str(rgb)
        for col,text in enumerate((data['name'],rgb,str(data.get('tolerance',45))),1):self.table.setItem(row,col,QTableWidgetItem(text))
        self.table.setCurrentCell(row,1)
    def move_row(self,delta):
        row=self.table.currentRow();target=row+delta
        if row<0 or not 0<=target<self.table.rowCount():return
        a=[self.table.takeItem(row,col) for col in range(4)];b=[self.table.takeItem(target,col) for col in range(4)]
        for col in range(4):self.table.setItem(row,col,b[col]);self.table.setItem(target,col,a[col])
        self.table.setCurrentCell(target,1)
    def delete_row(self):
        if self.table.currentRow()>=0:self.table.removeRow(self.table.currentRow())
    def menu(self,position):
        item=self.table.itemAt(position)
        if item is None:return
        self.table.setCurrentCell(item.row(),item.column());menu=QMenu(self)
        up=menu.addAction('上移');up.setEnabled(item.row()>0);up.triggered.connect(lambda:self.move_row(-1))
        down=menu.addAction('下移');down.setEnabled(item.row()<self.table.rowCount()-1);down.triggered.connect(lambda:self.move_row(1));menu.addSeparator()
        for title,col in [('修改名字',1),('修改色值',2),('修改容差',3)]:
            action=menu.addAction(title);action.triggered.connect(lambda checked=False,c=col:self.table.editItem(self.table.item(self.table.currentRow(),c)))
        menu.exec_(self.table.viewport().mapToGlobal(position))
    def collect(self):
        rows=[];names=[]
        for row in range(self.table.rowCount()):
            enabled=self.table.item(row,0).checkState()==Qt.Checked
            name=self.table.item(row,1).text().strip();raw=self.table.item(row,2).text().replace('，',',')
            if not name or any(c in name for c in ';；'):raise ValueError(f'第 {row+1} 行名称不能为空或含分号')
            rgb=rgb_value(raw)
            if ',' in name or '，' in name:
                rgb_value(name);name=','.join(map(str,rgb))
            tolerance=int(self.table.item(row,3).text())
            if not 5<=tolerance<=100:raise ValueError('颜色容差应在 5 到 100 之间')
            if enabled:
                if name in names:raise ValueError('启用的颜色名称不能重复')
                names.append(name)
            rows.append({'name':name,'rgb':list(rgb),'tolerance':tolerance,'enabled':enabled})
        return ';'.join(names),json.dumps(rows,ensure_ascii=False)
    def accept(self):
        try:self.value,self.config=self.collect()
        except (ValueError,TypeError) as error:QMessageBox.warning(self,'请检查颜色设置',str(error));return
        super().accept()
