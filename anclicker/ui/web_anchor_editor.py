"""Visual editor for multiple web anchors; preview never clicks the page."""
from anclicker.domain.web_locators import ANCHOR_RELATIONS, LOCATOR_METHODS, parse_anchor_config, encode_anchor_config
from anclicker.ui.web_window_selector import WebWindowSelector
from anclicker.ui.settings_combo import compact_web_combo_buttons
from anclicker.platform.qt_compat.QtCore import Qt
from anclicker.platform.qt_compat.QtWidgets import QComboBox, QDialog, QDialogButtonBox, QFormLayout, QHBoxLayout, QHeaderView, QLabel, QLineEdit, QMessageBox, QPushButton, QSpinBox, QTableWidget, QTableWidgetItem, QVBoxLayout


class WebAnchorDialog(QDialog):
    def __init__(self, parameters, pick_element, preview, parent=None, list_windows=None):
        super().__init__(parent)
        self.setWindowTitle('网页锚点定位')
        self.resize(880,620)
        self.pick_element, self.preview = pick_element, preview
        self.config = parse_anchor_config(parameters.get('anchor',''),parameters.get('anchorRel','下方'))
        layout=QVBoxLayout(self)
        hint=QLabel('先选目标，再添加附近稳定的文字或元素作为锚点。每个锚点都参与定位；预览以橙框标锚点、绿框标目标。',self)
        hint.setWordWrap(True);layout.addWidget(hint)
        form=QFormLayout();form.setFieldGrowthPolicy(QFormLayout.AllNonFixedFieldsGrow)
        self.window_selector=None
        if list_windows is not None:
            self.window_selector=WebWindowSelector(list_windows,parameters.get('browserWindow'),self)
            form.addRow('网页窗口',self.window_selector)
        target_row=QHBoxLayout();self.target=QLineEdit(str(parameters.get('selector','')),self)
        self.target.setPlaceholderText('例如 input、button.save、text=保存，或直接拾取目标')
        target_row.addWidget(self.target,1)
        self.target_by=QComboBox(self);self.target_by.addItems(LOCATOR_METHODS)
        self.target_by.setCurrentText(self.config['targetBy']);target_row.addWidget(self.target_by)
        target_pick=QPushButton('拾取目标',self);target_pick.clicked.connect(self._pick_target);target_row.addWidget(target_pick)
        form.addRow('目标元素',target_row);layout.addLayout(form)
        self.table=QTableWidget(0,3,self)
        self.table.setHorizontalHeaderLabels(['锚点定位方式','稳定文字／选择器','目标相对锚点'])
        self.table.setSelectionBehavior(QTableWidget.SelectRows)
        self.table.horizontalHeader().setSectionResizeMode(1,QHeaderView.Stretch)
        self.table.setColumnWidth(0,130);self.table.setColumnWidth(2,150)
        layout.addWidget(self.table,1)
        for rule in self.config['anchors']: self.add_anchor(rule)
        toolbar=QHBoxLayout()
        add=QPushButton('添加文字锚点',self);add.clicked.connect(lambda:self.add_anchor({'selector':'','by':'文本内容','relation':'右侧'}));toolbar.addWidget(add)
        pick=QPushButton('拾取并添加锚点',self);pick.clicked.connect(self._pick_anchor);toolbar.addWidget(pick)
        remove=QPushButton('删除选中锚点',self);remove.clicked.connect(self._remove);toolbar.addWidget(remove);toolbar.addStretch()
        layout.addLayout(toolbar)
        options=QFormLayout();options.setFieldGrowthPolicy(QFormLayout.AllNonFixedFieldsGrow)
        self.distance=QSpinBox(self);self.distance.setRange(0,100000);self.distance.setSpecialValueText('不限距离');self.distance.setSuffix(' 像素');self.distance.setValue(int(self.config['maxDistance']))
        self.index=QSpinBox(self);self.index.setRange(0,10000);self.index.setSpecialValueText('自动（有歧义时提示）');self.index.setValue(self.config['matchIndex'])
        self.index.setToolTip('指定第几个候选时，按页面从上到下、从左到右排序；0 为自动判断。')
        options.addRow('最大距离',self.distance);options.addRow('匹配序号',self.index);layout.addLayout(options)
        self.status=QLabel('可先预览匹配结果，再保存。目标与所有锚点须在同一网页框架。',self);self.status.setWordWrap(True);layout.addWidget(self.status)
        footer=QHBoxLayout();check=QPushButton('预览定位（不执行操作）',self);check.clicked.connect(self._preview);footer.addWidget(check);footer.addStretch()
        buttons=QDialogButtonBox(QDialogButtonBox.Ok|QDialogButtonBox.Cancel,self);buttons.button(QDialogButtonBox.Ok).setText('确定');buttons.button(QDialogButtonBox.Cancel).setText('取消');buttons.accepted.connect(self.accept);buttons.rejected.connect(self.reject);footer.addWidget(buttons);layout.addLayout(footer)
        compact_web_combo_buttons(self)
        for button in self.findChildren(QPushButton):button.setMinimumHeight(32)
        for control in (self.target,self.target_by,self.distance,self.index):control.setMinimumHeight(32)

    def add_anchor(self, rule):
        if self.table.rowCount()>=20:
            self.status.setText('最多支持 20 个锚点');return
        row=self.table.rowCount();self.table.insertRow(row)
        method=QComboBox(self.table);method.addItems(LOCATOR_METHODS);method.setCurrentText(rule.get('by','智能匹配'))
        relation=QComboBox(self.table);relation.addItems(ANCHOR_RELATIONS);relation.setCurrentText(rule.get('relation','右侧'))
        self.table.setCellWidget(row,0,method);self.table.setItem(row,1,QTableWidgetItem(rule.get('selector','')));self.table.setCellWidget(row,2,relation)
        self.table.setRowHeight(row,36)
        compact_web_combo_buttons(self.table)

    def _pick_target(self):
        try:
            result=self.pick_element(self.window_selector.selection()) if self.window_selector is not None else self.pick_element()
            if result:
                self.target.setText(str(result.get('anchorSelector') or result.get('css') or result.get('xpath') or ''))
                self.target_by.setCurrentText('智能匹配')
        except Exception as error:QMessageBox.warning(self,'拾取未完成',str(error))

    def _pick_anchor(self):
        try:
            result=self.pick_element()
            if result:
                stable_text=result.get('text','') if result.get('tag') in ('LABEL','SPAN','TD','TH','P','H1','H2','H3','BUTTON') else ''
                use_text=bool(stable_text and len(stable_text)<=80)
                self.add_anchor({'selector':stable_text if use_text else str(result.get('css') or result.get('xpath') or ''),
                                 'by':'文本内容' if use_text else 'CSS选择器' if result.get('css') else 'XPath', 'relation':'右侧'})
        except Exception as error:QMessageBox.warning(self,'拾取未完成',str(error))

    def _remove(self):
        for row in sorted({index.row() for index in self.table.selectedIndexes()},reverse=True):self.table.removeRow(row)

    def parameters(self):
        rules=[{'selector':self.table.item(row,1).text().strip(), 'by':self.table.cellWidget(row,0).currentText(), 'relation':self.table.cellWidget(row,2).currentText()} for row in range(self.table.rowCount())]
        if not rules:raise ValueError('请至少添加一个锚点')
        config={'anchors':rules,'targetBy':self.target_by.currentText(),'maxDistance':self.distance.value(),'matchIndex':self.index.value()}
        anchor=encode_anchor_config(config)
        return {'browserWindow':self.window_selector.selection() if self.window_selector is not None else None,'selector':self.target.text().strip(),'anchor':anchor,'by':'锚点定位','anchorRel':rules[0]['relation'] if rules[0]['relation'] in ('下方','上方','右侧','左侧','内部','相邻') else '下方'}

    def _preview(self):
        try:
            result=self.preview(self.parameters())
            if result:
                counts='；'.join('锚点'+str(i+1)+': '+str(item['count'])+' 个' for i,item in enumerate(result.get('anchors',[])))
                self.status.setText(result.get('reason','')+'；目标候选 '+str(result.get('count',0))+' 个'+('；'+counts if counts else ''))
        except Exception as error:QMessageBox.warning(self,'无法预览',str(error))

    def accept(self):
        try:self.parameters()
        except Exception as error:
            QMessageBox.warning(self,'锚点设置无效',str(error));return
        super().accept()
