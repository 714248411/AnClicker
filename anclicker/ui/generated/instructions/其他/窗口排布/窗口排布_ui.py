"""Two-column window arrangement form, shared by tool and instruction editor."""
from anclicker.platform.qt_compat.QtCore import Qt
from anclicker.platform.qt_compat.QtWidgets import QWidget,QVBoxLayout,QHBoxLayout,QFormLayout,QLabel,QLineEdit,QPushButton,QSplitter,QTreeWidget,QComboBox,QSpinBox,QCheckBox,QGroupBox,QDialogButtonBox,QScrollArea,QAbstractItemView
from anclicker.instructions.其他.窗口排布.schema import FIELDS

class Ui_InstructionEditor:
    def setupUi(self,dialog):
        self.rootLayout=QVBoxLayout(dialog);self.rootLayout.setContentsMargins(12,12,12,12);self.rootLayout.setSpacing(10)
        self.titleLabel=QLabel('窗口排布',dialog);self.titleLabel.setStyleSheet('font-size:18px;font-weight:600;');self.rootLayout.addWidget(self.titleLabel)
        self.splitter=QSplitter(Qt.Horizontal,dialog);self.splitter.setChildrenCollapsible(False)
        left=QWidget(self.splitter);left.setMinimumWidth(290);left_layout=QVBoxLayout(left);left_layout.setContentsMargins(0,0,8,0)
        search=QHBoxLayout();self.searchEdit=QLineEdit(left);self.searchEdit.setPlaceholderText('关键词搜索窗口标题、进程或类名');self.searchEdit.setClearButtonEnabled(True);search.addWidget(self.searchEdit,1)
        self.refreshButton=QPushButton('刷新',left);search.addWidget(self.refreshButton);left_layout.addLayout(search)
        selection=QHBoxLayout();self.selectAll=QCheckBox('全选当前列表',left);selection.addWidget(self.selectAll);self.countLabel=QLabel('已选 0 / 0',left);selection.addWidget(self.countLabel);selection.addStretch();self.sortButton=QPushButton('按名称排序',left);selection.addWidget(self.sortButton);left_layout.addLayout(selection)
        self.windowTree=QTreeWidget(left);self.windowTree.setHeaderLabels(['窗口名称','大小']);self.windowTree.setRootIsDecorated(False);self.windowTree.setSelectionMode(QAbstractItemView.SingleSelection);self.windowTree.setAlternatingRowColors(True);self.windowTree.setColumnWidth(0,260);self.windowTree.setColumnWidth(1,85);self.windowTree.setUniformRowHeights(True);self.windowTree.setObjectName('arrangementWindowTree');left_layout.addWidget(self.windowTree,1)
        order=QHBoxLayout();self.upButton=QPushButton('上移',left);self.downButton=QPushButton('下移',left);order.addWidget(self.upButton);order.addWidget(self.downButton);self.clearChecksButton=QPushButton('清除勾选',left);self.clearChecksButton.setToolTip('清除全部窗口的勾选，包括搜索后隐藏的窗口');order.addWidget(self.clearChecksButton);order.addStretch();left_layout.addLayout(order)
        left_hint=QLabel('勾选要排布的窗口，可上移／下移调整先后顺序。搜索只筛选列表，不清除已勾选项。',left);left_hint.setWordWrap(True);left_layout.addWidget(left_hint)
        right=QWidget(self.splitter);right.setMinimumWidth(380);right_layout=QVBoxLayout(right);right_layout.setContentsMargins(8,0,0,0)
        settings=QWidget(right);settings.setObjectName('instructionEditorBody');self.parameterFormLayout=QVBoxLayout(settings);self.parameterFormLayout.setAlignment(Qt.AlignTop);self.parameterFormLayout.setSpacing(10);self.parameterFormLayout.setContentsMargins(4,4,8,8)
        for i,field in enumerate(FIELDS):
            if field.key=='屏幕':control=QComboBox(settings);control.addItem('主屏幕','主屏幕')
            elif field.kind=='choice':control=QComboBox(settings);control.addItems(field.choices);control.setCurrentText(str(field.default))
            elif field.kind=='int':control=QSpinBox(settings);control.setRange(int(field.minimum),int(field.maximum));control.setValue(int(field.default))
            elif field.kind=='bool':control=QCheckBox('启用',settings);control.setChecked(bool(field.default))
            else:control=QLineEdit(str(field.default),settings)
            control.setObjectName('parameter_'+str(i));setattr(self,'parameter_'+str(i),control)
        self.parameter_0.setMaxLength(250000);self.parameter_0.hide();self.parameter_18.hide()
        self.modeRows={};self.modeRowWidgets={}
        def add_row(key,label,field):
            caption=QLabel(label,settings);caption.setWordWrap(True)
            label_width=max(90,caption.fontMetrics().horizontalAdvance('首窗左上角')+12);caption.setMinimumWidth(label_width);caption.setMaximumWidth(label_width)
            if isinstance(field,QHBoxLayout):
                container=QWidget(settings);container.setLayout(field);field=container
            row=QWidget(settings);row_layout=QHBoxLayout(row);row_layout.setContentsMargins(0,0,0,0);row_layout.setSpacing(10);row_layout.addWidget(caption);row_layout.addWidget(field,1)
            self.parameterFormLayout.addWidget(row);self.modeRows[key]=(caption,field);self.modeRowWidgets[key]=row
        screen_row=QHBoxLayout();screen_row.setContentsMargins(0,0,0,0);screen_row.addWidget(self.parameter_1,1);self.screenRefreshButton=QPushButton('刷新',settings);screen_row.addWidget(self.screenRefreshButton);add_row('screen','屏幕选择',screen_row)
        add_row('mode','排布方式',self.parameter_2)
        self.modeHint=QLabel('',settings);self.modeHint.setWordWrap(True);self.modeHint.setObjectName('mutedText');add_row('hint','',self.modeHint)
        add_row('size','窗口大小',self.parameter_3)
        self.customSizeRow=QWidget(settings);custom=QHBoxLayout(self.customSizeRow);custom.setContentsMargins(0,0,0,0);custom.addWidget(QLabel('宽'));custom.addWidget(self.parameter_4);custom.addWidget(QLabel('高'));custom.addWidget(self.parameter_5);add_row('custom_size','自定义尺寸',self.customSizeRow)
        add_row('direction','排布方向',self.parameter_6)
        self.gridRow=QWidget(settings);grid=QHBoxLayout(self.gridRow);grid.setContentsMargins(0,0,0,0);grid.addWidget(QLabel('行'));grid.addWidget(self.parameter_7);grid.addWidget(QLabel('列'));grid.addWidget(self.parameter_8);self.autoGridButton=QPushButton('自动计算',settings);grid.addWidget(self.autoGridButton);add_row('grid','行列设置',self.gridRow)
        gaps=QHBoxLayout();gaps.setContentsMargins(0,0,0,0);gaps.addWidget(QLabel('边距'));gaps.addWidget(self.parameter_9);gaps.addWidget(QLabel('间距'));gaps.addWidget(self.parameter_10);add_row('gaps','留白（像素）',gaps)
        origin=QHBoxLayout();origin.setContentsMargins(0,0,0,0);origin.addWidget(QLabel('X'));origin.addWidget(self.parameter_13);origin.addWidget(QLabel('Y'));origin.addWidget(self.parameter_14);self.originButton=QPushButton('屏幕左上角',settings);origin.addWidget(self.originButton);add_row('origin','首窗左上角',origin)
        add_row('x_step','X 间距（像素）',self.parameter_15)
        add_row('y_step','Y 间距（像素）',self.parameter_16)
        add_row('diagonal_step','斜向间距（像素）',self.parameter_17)
        for control in (self.parameter_13,self.parameter_14):control.setToolTip('桌面绝对坐标，可填负数，支持左侧／上方的副屏。')
        self.parameter_15.setToolTip('后一个窗口左上角 X − 前一个窗口左上角 X；负数向左。')
        self.parameter_16.setToolTip('后一个窗口左上角 Y − 前一个窗口左上角 Y；负数向上。')
        self.parameter_17.setToolTip('每一步 X 和 Y 同时增加此值；负数向左上。')
        add_row('aspect','游戏增强模式',self.parameter_12)
        self.parameter_12.setText('保持窗口内容比例，避免拉伸')
        add_row('auto_fill','自动补位',self.parameter_11)
        self.parameter_11.setText('启用（持续到停止补位或退出）')
        self.parameter_11.setToolTip('持续观察已选程序：窗口关闭后，仅用同程序、同窗口类的新窗口填补原位置；不移动起初未勾选的窗口。启用后持续运行，直到停止补位或退出 AnClicker。')
        self.settingsScroll=QScrollArea(right);scroll=self.settingsScroll;scroll.setWidgetResizable(True);scroll.setFrameShape(QScrollArea.NoFrame);scroll.setWidget(settings);right_layout.addWidget(scroll,1)
        self.previewTitle=QPushButton('收起排布预览 ▴',right);self.previewTitle.setFlat(True);self.previewTitle.setObjectName('arrangementPreviewToggle');right_layout.addWidget(self.previewTitle);self.previewHolder=QVBoxLayout();right_layout.addLayout(self.previewHolder)
        self.statusLabel=QLabel('先勾选窗口，再预览或立即排布。',right);self.statusLabel.setWordWrap(True);right_layout.addWidget(self.statusLabel)
        self.autoStatus=QLabel('自动补位未启动',right);self.autoStatus.setWordWrap(True);right_layout.addWidget(self.autoStatus)
        self.autoStatus.hide()
        actions=QHBoxLayout();self.applyButton=QPushButton('立即排布',right);self.applyButton.setObjectName('accentButton');self.stopButton=QPushButton('停止自动补位',right);actions.addWidget(self.applyButton);actions.addWidget(self.stopButton);right_layout.addLayout(actions)
        self.splitter.addWidget(left);self.splitter.addWidget(right);self.splitter.setStretchFactor(0,4);self.splitter.setStretchFactor(1,6);self.rootLayout.addWidget(self.splitter,1)
        self.commonGroupBox=QGroupBox('通用参数',dialog);common=QHBoxLayout(self.commonGroupBox)
        self.repeatSpinBox=QSpinBox(dialog);self.repeatSpinBox.setRange(1,999999);self.repeatSpinBox.setValue(1);common.addWidget(QLabel('重复次数'));common.addWidget(self.repeatSpinBox)
        self.errorPolicyComboBox=QComboBox(dialog);self.errorPolicyComboBox.addItems(['自动跳过','提示异常并暂停','提示异常并停止']);self.errorPolicyComboBox.setCurrentIndex(1);common.addWidget(QLabel('异常处理'));common.addWidget(self.errorPolicyComboBox)
        self.noteEdit=QLineEdit(dialog);common.addWidget(QLabel('备注'));common.addWidget(self.noteEdit,1);self.rootLayout.addWidget(self.commonGroupBox)
        self.footerLayout=QHBoxLayout();self.testButton=QPushButton('测试指令',dialog);self.footerLayout.addWidget(self.testButton);self.footerLayout.addStretch()
        self.buttonBox=QDialogButtonBox(QDialogButtonBox.Ok|QDialogButtonBox.Cancel,dialog);self.footerLayout.addWidget(self.buttonBox);self.rootLayout.addLayout(self.footerLayout)
