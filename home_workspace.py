"""Project-oriented home page; reuse guarded project actions."""
from qt_compat.QtCore import Qt
from qt_compat.QtWidgets import (QWidget, QScrollArea, QVBoxLayout,
    QGridLayout, QLabel, QPushButton, QListWidget, QListWidgetItem, QFileDialog,
    QFrame, QSizePolicy)
from recording_layout import control_row
from recent_projects import short_path


class HomeWorkspace(QScrollArea):
    def __init__(self, view):
        super().__init__()
        self.view = view
        self.setObjectName('homeWorkspace')
        self.setWidgetResizable(True)
        self.setFrameShape(QFrame.NoFrame)
        self.setHorizontalScrollBarPolicy(Qt.ScrollBarAlwaysOff)
        body = QWidget()
        body.setObjectName('mainWorkspacePage')
        self.setWidget(body)
        layout = QVBoxLayout(body)
        layout.setContentsMargins(12, 8, 12, 12)
        layout.setSpacing(10)
        title = QLabel('自动化工作台')
        title.setObjectName('homePageTitle')
        layout.addWidget(title)
        current, current_layout = view._card('当前项目')
        self.project = QLabel('未关联项目文件')
        self.project.setObjectName('sectionTitle')
        self.project.setWordWrap(True)
        current_layout.addWidget(self.project)
        self.summary = QLabel()
        self.summary.setObjectName('mutedText')
        self.summary.setWordWrap(True)
        current_layout.addWidget(self.summary)
        actions = control_row()
        self.open_button = QPushButton('打开项目…')
        self.open_button.setObjectName('accentButton')
        self.open_button.clicked.connect(self.open_project)
        self.save_button = QPushButton('保存项目')
        self.save_button.clicked.connect(self.save_project)
        self.continue_button = QPushButton('继续编辑流程图')
        self.continue_button.clicked.connect(view.show_flow)
        for button in (self.open_button, self.save_button, self.continue_button):
            actions.addWidget(button)
        current_layout.addLayout(actions)
        layout.addWidget(current)
        heading = QLabel('常用工作入口')
        heading.setObjectName('sectionTitle')
        layout.addWidget(heading)
        self.grid = QGridLayout()
        self.grid.setSpacing(10)
        self.entries = []
        for title, description, callback in (
            ('表格图', '批量维护指令、参数和执行顺序', view.show_table),
            ('流程图', '编排步骤、条件分支与循环', view.show_flow),
            ('多功能', '编辑代码，与表格和流程同步', view.show_code),
            ('键鼠录制', '录下桌面操作，预览后生成指令', view.show_recording),
            ('网页录制', '录下网页操作，生成元素定位指令', view.show_web_recording),
            ('变量管理', '管理流程共用的变量与默认值', view.show_variables),
        ):
            button = QPushButton(title + '\n' + description)
            button.setObjectName('homeEntry')
            button.setToolTip(description)
            button.setMinimumWidth(0)
            button.setSizePolicy(QSizePolicy.Ignored, QSizePolicy.Preferred)
            button.setMinimumHeight(76)
            button.clicked.connect(callback)
            self.entries.append(button)
        self._columns = 0
        self._arrange(2)
        layout.addLayout(self.grid)
        recent, recent_layout = view._card('最近项目', '双击打开项目，也可以将 .xlsx 文件拖入窗口。')
        self.recent = QListWidget()
        self.recent.setObjectName('homeRecentProjects')
        self.recent.setMinimumWidth(0)
        self.recent.setHorizontalScrollBarPolicy(Qt.ScrollBarAlwaysOff)
        self.recent.setTextElideMode(Qt.ElideMiddle)
        self.recent.itemActivated.connect(self.open_recent)
        recent_layout.addWidget(self.recent)
        layout.addWidget(recent)
        layout.addStretch(1)

    def _arrange(self, columns):
        if columns == self._columns:
            return
        self._columns = columns
        for button in self.entries:
            self.grid.removeWidget(button)
        for index, button in enumerate(self.entries):
            self.grid.addWidget(button, index // columns, index % columns)
        self.grid.setColumnStretch(0, 1)
        self.grid.setColumnStretch(1, 1 if columns == 2 else 0)

    def resizeEvent(self, event):
        super().resizeEvent(event)
        self._arrange(2 if self.viewport().width() >= 650 else 1)

    def save_project(self):
        self.view.window.save_data('自动保存')
        self.refresh_projects()

    def open_project(self):
        path, _ = QFileDialog.getOpenFileName(self, '打开项目', '', 'An Clicker 项目 (*.xlsx)')
        if path:
            self.view.window.open_project_path(path)
            self.refresh_projects()

    def open_recent(self, item):
        path = item.data(Qt.UserRole)
        if path:
            self.view.window.open_recent_file(path)
            self.refresh_projects()

    def refresh_projects(self):
        db = self.view.window.db
        current = db.get_setting_value('当前文件路径')
        current = str(current) if current and current != 'None' else ''
        self.project.setText(short_path(current) if current else '未关联项目文件 · 可直接编辑当前流程')
        self.project.setToolTip(current)
        paths = list(dict.fromkeys(db.get_recently_opened_file('文件列表') or []))[:5]
        self.recent.clear()
        for path in paths:
            item = QListWidgetItem(short_path(path))
            item.setData(Qt.UserRole, path)
            item.setToolTip(path)
            self.recent.addItem(item)
        if not paths:
            item = QListWidgetItem('暂无最近项目，打开或保存项目后会显示在这里')
            item.setFlags(Qt.NoItemFlags)
            self.recent.addItem(item)
        self.recent.setFixedHeight(max(1, len(paths)) * 38 + 6)

    def showEvent(self, event):
        super().showEvent(event)
        self.refresh_projects()
