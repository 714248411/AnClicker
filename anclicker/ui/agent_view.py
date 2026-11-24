"""Responsive, conversation-first local Agent page."""
import json
from uuid import uuid4
from datetime import datetime
from dataclasses import asdict
from pathlib import Path
from anclicker.platform.qt_compat.QtGui import QPixmap
from anclicker.platform.services import open_path
from anclicker.ui.path_drop import enable_path_drop
from copy import deepcopy
from anclicker.platform.qt_compat.QtCore import Qt, QThread, Signal, QTimer
from anclicker.platform.qt_compat.QtWidgets import (QWidget,QFrame,QVBoxLayout,QHBoxLayout,QBoxLayout,QLabel,
    QPushButton,QToolButton,QPlainTextEdit,QLineEdit,QComboBox,QSpinBox,QFormLayout,
    QScrollArea,QSizePolicy,QTabWidget,QTableWidget,QTableWidgetItem,QHeaderView,
    QAbstractItemView,QMessageBox,QFileDialog,QDialog,QLayout,QMenu,QGridLayout)
from anclicker.execution.services import RuntimeDependencies
from anclicker.execution.actions import wait_interruptibly
from anclicker.domain.instructions import ExecutionContext, InstructionDraft
from anclicker.instructions.registry import get_instruction_spec
from anclicker.domain.agent_protocol import draft_data, export_drafts, make_draft
from models.agent_provider import AgentSettings, ModelClient
from models.agent_factory import create_agent_session
from anclicker.app.state import application_state

from anclicker._imports import DeferredImports as _DeferredImports

# Dependencies declared here retain their existing on-demand loading boundaries.
_module_imports = _DeferredImports(globals(), {
    'LocalModelDialog': ('from', 'anclicker.ui.local_model_dialog', ('LocalModelDialog',), 0),
    'start_local_model': ('from', 'models.agent_local', ('start_local_model',), 0),
    'Path': ('from', 'pathlib', ('Path',), 0),
    '_manager': ('from', 'models.agent_local', ('_manager',), 0),
    'local_snapshot': ('from','models.agent_local',('local_snapshot',),0),
    'stop_local_model': ('from', 'models.agent_local', ('stop_local_model',), 0),
})


class AgentWorker(QThread):
    progress=Signal(str,object)
    def __init__(self,session,text,settings,parent,action='chat'):
        super().__init__(parent)
        self.session,self.text,self.settings,self.action=session,text,settings,action
        self.context=ExecutionContext();self.error=None
        self.context.output=lambda message:self.progress.emit('status',message)
        if hasattr(parent,'window'):
            database=parent.window.db
            wait=lambda seconds:wait_interruptibly(self.context,seconds)
            self.context.metadata.update(database=database,wait_interruptibly=wait)
            self.context.runtime=RuntimeDependencies(database=database,wait=wait,ocr_pool=getattr(parent.window,'ocr_pool',None))
    def run(self):
        try:
            local=(not hasattr(self.session,'api_url') and self.settings.backend=='compatible'
                   and self.settings.endpoint.rstrip('/')=='http://127.0.0.1:8766/v1'
                   and self.settings.model=='anclicker-small')
            if self.action!='local' and not local:
                stop_local_model = _module_imports.load('stop_local_model')
                try:stop_local_model(adopt=False)
                except RuntimeError:pass  # An active request keeps its lease until completion.
            if self.action=='local':
                start_local_model = _module_imports.load('start_local_model')
                self.progress.emit('local_status',start_local_model(self.settings.local_profile,self.context,self.settings.idle_seconds))
            elif self.action=='models':self.progress.emit('models',ModelClient(self.settings).models(self.context))
            else:self.session.run(self.text,self.settings,self.context,self.progress.emit)
        except InterruptedError:self.progress.emit('status','已停止 · 已完成的步骤和草稿保留')
        except Exception as error:
            self.error=str(error);self.progress.emit('error',self.error)

class Composer(QPlainTextEdit):
    submitted=Signal()
    def __init__(self,parent=None):
        super().__init__(parent)
        enable_path_drop(self,insert=True,multiple=True)
        self.setToolTip('可拖入文件或文件夹，在当前输入光标处插入完整路径；多个路径分行显示。')
    def keyPressEvent(self,event):
        if event.key() in (Qt.Key_Return,Qt.Key_Enter) and not (event.modifiers() & Qt.ShiftModifier):
            self.submitted.emit();event.accept();return
        super().keyPressEvent(event)

class AgentView(QWidget):
    def __init__(self,window):
        super().__init__(window)
        self.window=window;self.session=create_agent_session();self.worker=None;self.written=False
        self._chat_id=uuid4().hex;self._chat_events=[];self._restoring=False;self._history=[]
        self._load_history()
        self.setObjectName('agentPage');self.setAttribute(Qt.WA_StyledBackground,True);self._cards=[];self._tool_card=None
        root=QVBoxLayout(self);root.setContentsMargins(14,12,14,12);root.setSpacing(12)
        header=self.header=QBoxLayout(QBoxLayout.LeftToRight)
        identity=self.identity=QBoxLayout(QBoxLayout.LeftToRight)
        self.action_bar=QWidget();self.action_bar.setMinimumWidth(0)
        actions=self.action_grid=QGridLayout(self.action_bar);actions.setContentsMargins(0,0,0,0)
        header.addLayout(identity,1);header.addWidget(self.action_bar,1,Qt.AlignRight|Qt.AlignTop)
        brand=self.brand=QLabel('✦  AnClicker');brand.setObjectName('agentBrand');identity.addWidget(brand)
        self.badge=QPushButton('本机模型 ▾');self.badge.setObjectName('agentBadge');self.badge.setCursor(Qt.PointingHandCursor);self.badge.setMinimumWidth(0);self.badge.setSizePolicy(QSizePolicy.Preferred,QSizePolicy.Preferred);self.badge.setToolTip('点击管理本地模型：切换、新增、删除');self.badge.clicked.connect(self.manage_local_models);identity.addWidget(self.badge);identity.addStretch()
        self.new_button=QPushButton('新对话');self.drafts_button=QPushButton('草稿 0');self.settings_button=QPushButton('设置')
        self.history_button=QPushButton('历史对话');self.history_menu=QMenu(self.history_button)
        self.history_menu.setObjectName('agentHistoryMenu');self.history_menu.setToolTipsVisible(True)
        self.history_menu.setContextMenuPolicy(Qt.CustomContextMenu);self.history_menu.customContextMenuRequested.connect(self.history_context_menu)
        self.history_button.setToolTip('恢复最近 20 条对话与对应草稿；右键删除')
        self.new_button.setToolTip('保存当前对话并开始新对话')
        self.history_button.setMenu(self.history_menu);self.history_menu.aboutToShow.connect(self._refresh_history_menu)
        self.header_buttons=(self.new_button,self.history_button,self.drafts_button,self.settings_button)
        for column,b in enumerate(self.header_buttons):
            b.setMinimumWidth(0);b.setCursor(Qt.PointingHandCursor)
            b.setSizePolicy(QSizePolicy.Ignored,QSizePolicy.Preferred)
            actions.addWidget(b,0,column)
        actions.setSpacing(6)
        root.addLayout(header)
        self.body=QBoxLayout(QBoxLayout.LeftToRight);self.body.setSpacing(12);root.addLayout(self.body,1)
        self.chat=QWidget();self.chat.setMinimumWidth(0);chat=QVBoxLayout(self.chat);chat.setContentsMargins(0,0,0,0);chat.setSpacing(10)
        self.body.addWidget(self.chat,1)
        self.scroll=QScrollArea();self.scroll.setWidgetResizable(True);self.scroll.setFrameShape(QFrame.NoFrame)
        self.scroll.setHorizontalScrollBarPolicy(Qt.ScrollBarAlwaysOff)
        self._follow_chat_bottom = True
        self._scroll_timer = QTimer(self)
        self._scroll_timer.setSingleShot(True)
        self._scroll_timer.timeout.connect(self._apply_scroll_bottom)
        self.scroll.verticalScrollBar().rangeChanged.connect(self._chat_range_changed)
        self.scroll.verticalScrollBar().valueChanged.connect(self._chat_scroll_changed)
        self.messages=QWidget();self.message_layout=QVBoxLayout(self.messages);self.message_layout.setContentsMargins(2,8,2,8);self.message_layout.setSpacing(14)
        self.message_layout.addStretch();self.scroll.setWidget(self.messages);chat.addWidget(self.scroll,1)
        self.status=QLabel('准备就绪 · 私有 API 模式' if hasattr(self.session,'api_url') else '准备就绪 · 模型按需运行');self.status.setObjectName('agentStatus');self.status.setWordWrap(True);chat.addWidget(self.status)
        composer=QFrame();composer.setObjectName('agentComposer');box=QVBoxLayout(composer);box.setContentsMargins(12,8,12,8)
        self.input=Composer();self.input.setPlaceholderText('例如：打开百度，搜索热点；把当前表格按表头对应填入网页…');self.input.setFixedHeight(66);self.input.setFrameShape(QFrame.NoFrame);box.addWidget(self.input)
        bottom=QHBoxLayout();hint=self.input_hint=QLabel('Enter 发送 · Shift + Enter 换行');hint.setObjectName('agentHint');bottom.addWidget(hint);bottom.addStretch()
        self.stop_button=QPushButton('停止');self.send_button=QPushButton('发送 ↑');self.send_button.setObjectName('accentButton')
        bottom.addWidget(self.stop_button);bottom.addWidget(self.send_button);box.addLayout(bottom);chat.addWidget(composer)
        self.details=QTabWidget();self.details.setMinimumWidth(0);self.details.setMaximumWidth(440);self.body.addWidget(self.details)
        self._build_drafts();self._build_settings();self.details.setCurrentIndex(1);self.details.show()
        self.new_button.clicked.connect(self.new_chat);self.drafts_button.clicked.connect(lambda:self.toggle_details(0));self.settings_button.clicked.connect(lambda:self.toggle_details(1))
        self.send_button.clicked.connect(self.send);self.input.submitted.connect(self.send);self.stop_button.clicked.connect(self.stop)
        self._load_settings();self.welcome();self.update_buttons();self.apply_theme('dark')
        self.history_timer=QTimer(self);self.history_timer.setSingleShot(True);self.history_timer.setInterval(500);self.history_timer.timeout.connect(self._save_history)
        self.input.textChanged.connect(lambda:self.history_timer.start())
        if self._history:self._restore_chat(self._history[0]['id'],save_current=False)
        self.resource_timer=QTimer(self);self.resource_timer.setInterval(2000);self.resource_timer.timeout.connect(self.refresh_resources);self.resource_timer.start()
    def contextMenuEvent(self,event):
        manager=getattr(getattr(self.window,'view_workspace',None),'docking',None)
        if manager is not None:
            manager.panel_menu('agent',event.globalPos());event.accept()
        else:super().contextMenuEvent(event)
    def showEvent(self,event):
        super().showEvent(event)
        QTimer.singleShot(0,self._activate_local_model)
    def _activate_local_model(self):
        if not self.isVisible() or self.busy or hasattr(self.session,'api_url'):return
        if self.backend.currentData()!='compatible' or self.endpoint.text().rstrip('/')!='http://127.0.0.1:8766/v1':return
        self.start_local()
    @property
    def busy(self):return self.worker is not None
    @property
    def unsaved(self):return bool(self.session.drafts and not self.written)
    def _build_drafts(self):
        page=QWidget();page.setObjectName('agentDraftPage');layout=QVBoxLayout(page);layout.setContentsMargins(14,14,14,14);layout.setSpacing(10)
        title=QLabel('指令草稿');title.setObjectName('agentSection');layout.addWidget(title)
        hint=QLabel('双击修改参数；右键可删除、上移、下移。');hint.setWordWrap(True);layout.addWidget(hint)
        self.preview=QTableWidget(0,2);self.preview.setHorizontalHeaderLabels(['指令','参数'])
        self.preview.setSelectionBehavior(QAbstractItemView.SelectRows);self.preview.setEditTriggers(QAbstractItemView.NoEditTriggers)
        self.preview.horizontalHeader().setSectionResizeMode(1,QHeaderView.Stretch);self.preview.setMinimumWidth(0)
        self.preview.verticalHeader().hide();self.preview.setShowGrid(False);self.preview.setAlternatingRowColors(True)
        self.preview.verticalHeader().setDefaultSectionSize(38);layout.addWidget(self.preview,1)
        self.empty_drafts=QLabel('暂无草稿\n对话生成的指令会显示在这里');self.empty_drafts.setObjectName('agentEmptyState');self.empty_drafts.setAlignment(Qt.AlignCenter);self.empty_drafts.setMinimumHeight(80);layout.addWidget(self.empty_drafts,1)
        self.edit_button=QPushButton('编辑选中指令');self.write_button=QPushButton('写入表格与流程图');self.write_button.setObjectName('accentButton')
        self.export_button=QPushButton('导出标准 JSON');self.import_button=QPushButton('导入网页录制草稿');self.import_json_button=QPushButton('导入 API / JSON 草稿')
        for b in (self.edit_button,self.write_button,self.export_button,self.import_button,self.import_json_button):
            b.setMinimumHeight(36);layout.addWidget(b)
        self.draft_hint=QLabel('写入后可在流程图检查连线，再运行任务。');self.draft_hint.setWordWrap(True);layout.addWidget(self.draft_hint)
        draft_scroll=QScrollArea();draft_scroll.setObjectName('agentDraftScroll');draft_scroll.setWidgetResizable(True);draft_scroll.setFrameShape(QFrame.NoFrame)
        draft_scroll.setHorizontalScrollBarPolicy(Qt.ScrollBarAlwaysOff);draft_scroll.setWidget(page)
        self.details.addTab(draft_scroll,'草稿')
        order=QHBoxLayout();layout.addLayout(order)
        self.delete_draft_button=QPushButton('删除');self.move_up_button=QPushButton('上移 ↑');self.move_down_button=QPushButton('下移 ↓')
        for button in (self.delete_draft_button,self.move_up_button,self.move_down_button):order.addWidget(button)
        self.preview.setSelectionMode(QAbstractItemView.SingleSelection)
        self.delete_draft_button.clicked.connect(self.delete_draft)
        self.move_up_button.clicked.connect(lambda:self.move_draft(-1));self.move_down_button.clicked.connect(lambda:self.move_draft(1))
        self.preview.itemSelectionChanged.connect(self.update_draft_controls)
        self.preview.setContextMenuPolicy(Qt.CustomContextMenu);self.preview.customContextMenuRequested.connect(self.draft_context_menu)
        self.preview.cellDoubleClicked.connect(lambda *_:self.edit_draft());self.edit_button.clicked.connect(self.edit_draft)
        self.write_button.clicked.connect(self.write);self.export_button.clicked.connect(self.export);self.import_button.clicked.connect(self.import_recording);self.import_json_button.clicked.connect(self.import_json)
    def _build_settings(self):
        scroll=QScrollArea();scroll.setObjectName('agentSettingsScroll');scroll.setWidgetResizable(True);scroll.setFrameShape(QFrame.NoFrame)
        page=QWidget();page.setObjectName('agentSettingsPage');page.setAttribute(Qt.WA_StyledBackground,True);form=QFormLayout(page);form.setFieldGrowthPolicy(QFormLayout.AllNonFixedFieldsGrow);form.setRowWrapPolicy(QFormLayout.WrapAllRows)
        self.backend=QComboBox();self.backend.addItem('本地 / OpenAI 兼容','compatible');self.backend.addItem('Ollama','ollama')
        self.endpoint=QLineEdit();self.model=QComboBox();self.model.setEditable(True)
        self.mode=QComboBox();self.mode.addItem('标准 JSON · 小模型','json');self.mode.addItem('原生工具调用','native')
        self.key=QLineEdit();self.key.setEchoMode(QLineEdit.Password);self.key.setPlaceholderText('可选，仅本次会话保留')
        self.steps=QSpinBox();self.steps.setRange(1,30);self.timeout=QSpinBox();self.timeout.setRange(10,300);self.timeout.setSuffix(' 秒')
        for label,widget in [('服务类型',self.backend),('服务地址',self.endpoint),('模型名称',self.model),('调用格式',self.mode),('API Key',self.key),('每轮最多步骤',self.steps),('请求超时',self.timeout)]:form.addRow(label,widget)
        self.task_mode=QComboBox();self.task_mode.addItem('试运行 → 结果核验 → 草稿','verify');self.task_mode.addItem('仅生成草稿 · 不执行','draft');self.task_mode.addItem('直接调用工具 · 文件 / 网页 / 核验','direct');form.addRow('对话工作方式',self.task_mode)
        self.local_profile=QComboBox()
        for title,value in [('自动调度','auto'),('优先 CPU · 低占用','cpu'),('优先 GPU · 失败回退 CPU','gpu')]:self.local_profile.addItem(title,value)
        self.idle=QSpinBox();self.idle.setRange(180,180);self.idle.setSuffix(' 秒');self.idle.setToolTip('对话结束后空闲 3 分钟自动释放，下一次对话自动启动')
        form.addRow('本机计算资源',self.local_profile);form.addRow('空闲后释放模型',self.idle)
        self.refresh_button=QPushButton('检测连接 / 获取模型');form.addRow(self.refresh_button)
        self.manage_models_button=QPushButton('管理本地模型 · 切换 / 新增 / 删除');form.addRow(self.manage_models_button);self.manage_models_button.clicked.connect(self.manage_local_models)
        self.local_button=QPushButton('启动已准备的本机模型');form.addRow(self.local_button)
        self.unload_button=QPushButton('释放本机模型');form.addRow(self.unload_button)
        self.unload_button.clicked.connect(self.stop_local)
        self.model_note=QLabel('本机 Qwen 规划模型。打开 Agent 时自动启动，空闲 3 分钟后释放；调用外部接口时释放本机模型。低内存优先尝试可用显卡，失败回退 CPU。单任务排队，空闲自动释放。其他电脑先准备运行器和模型。');self.model_note.setWordWrap(True);form.addRow(self.model_note)
        self.refresh_button.clicked.connect(lambda:self.start_worker('',action='models'));self.local_button.clicked.connect(self.start_local)
        for widget in (self.backend,self.endpoint,self.model,self.mode,self.key,self.steps,self.timeout,self.task_mode,self.local_profile,self.idle,self.refresh_button,self.local_button,self.unload_button):
            widget.setMinimumWidth(0);widget.setSizePolicy(QSizePolicy.Ignored,QSizePolicy.Fixed)
        scroll.setHorizontalScrollBarPolicy(Qt.ScrollBarAlwaysOff)
        scroll.setWidget(page);self.details.addTab(scroll,'模型设置')
    def _load_settings(self):
        settings=asdict(AgentSettings())
        try:
            saved=json.loads(self.window.db.get_setting_value('对话Agent设置') or '{}')
            settings.update({k:v for k,v in saved.items() if k in settings and k not in ('api_key','idle_seconds')})
            AgentSettings(**settings).validate()
        except (ValueError,TypeError,AttributeError):settings=asdict(AgentSettings())
        self.task_mode.setCurrentIndex((0 if settings['verify_before_draft'] else 1) if settings['draft_only'] else 2)
        self.backend.setCurrentIndex(max(0,self.backend.findData(settings['backend'])));self.endpoint.setText(str(settings['endpoint']));self.model.setEditText(str(settings['model']))
        self.mode.setCurrentIndex(max(0,self.mode.findData(settings['mode'])));self.steps.setValue(int(settings['max_steps']));self.timeout.setValue(int(settings['timeout']));self.local_profile.setCurrentIndex(max(0,self.local_profile.findData(settings['local_profile'])));self.idle.setValue(int(settings['idle_seconds']))
    def settings(self):
        return AgentSettings(self.backend.currentData(),self.endpoint.text().strip(),self.model.currentText().strip(),self.mode.currentData(),self.steps.value(),self.timeout.value(),self.key.text().strip(),self.local_profile.currentData(),self.idle.value(),self.task_mode.currentData()!='direct',self.task_mode.currentData()=='verify').validate()
    def save_settings(self,settings):
        data=asdict(settings);data.pop('api_key',None)
        self.window.db.set_setting_value('对话Agent设置',json.dumps(data,ensure_ascii=False))
    def welcome(self):
        self.add_message('assistant','把想做的事，告诉我。\n\n默认先拆分并试运行，再核验实际结果。网页导航和百度搜索自动读取实际网址；文件夹任务自动定位并核验。其他任务可提供目标窗口标题和预期文字进行截图 OCR 核验。通过后自动加入草稿，失败则说明原因并询问是否保留。试运行会实际执行操作；也可在设置选择仅生成草稿。')
        frame=QFrame();layout=QVBoxLayout(frame);layout.setContentsMargins(8,0,8,8)
        for text in ('编写一条等待 2 秒的指令','打开 https://example.com 并查看页面','抓取 https://example.com 的正文'):
            b=QPushButton(text+'  ↗');b.setObjectName('agentSuggestion');b.setSizePolicy(QSizePolicy.Ignored,QSizePolicy.Fixed);b.clicked.connect(lambda _=False,t=text:self.input.setPlainText(t));layout.addWidget(b)
        self.message_layout.insertWidget(self.message_layout.count()-1,frame);self._cards.append(frame)
    def add_message(self,role,text):
        if not self._restoring:self._chat_events.append(['message',{'role':role,'text':str(text)}])
        row=QWidget();layout=QHBoxLayout(row);layout.setContentsMargins(0,0,0,0)
        bubble=QFrame();bubble.setObjectName('agentUser' if role=='user' else 'agentAssistant');bubble.setMaximumWidth(700)
        content=QVBoxLayout(bubble);content.setContentsMargins(14,12,14,12)
        title=QLabel('你' if role=='user' else '✦ AnClicker');title.setObjectName('agentHint');content.addWidget(title)
        label=QLabel(str(text));label.setTextFormat(Qt.PlainText);label.setWordWrap(True);label.setTextInteractionFlags(Qt.TextSelectableByMouse);label.setMinimumWidth(0);content.addWidget(label)
        if role=='user':layout.addStretch(1)
        layout.addWidget(bubble,5)
        if role!='user':layout.addStretch(1)
        self.message_layout.insertWidget(self.message_layout.count()-1,row);self._cards.append(row);self._trim_cards();self.scroll_bottom()
    def _trim_cards(self):
        while len(self._cards)>100:
            card=self._cards.pop(0);self.message_layout.removeWidget(card);card.deleteLater()
    def scroll_bottom(self):
        self._follow_chat_bottom = True
        self._scroll_timer.start(0)
    def _apply_scroll_bottom(self):
        if self._follow_chat_bottom:
            bar = self.scroll.verticalScrollBar()
            bar.setValue(bar.maximum())
    def _chat_range_changed(self, minimum, maximum):
        # Wrapped labels can settle over multiple layout passes after insertion.
        if self._follow_chat_bottom:
            self._scroll_timer.start(0)
    def _chat_scroll_changed(self, value):
        if not self._scroll_timer.isActive():
            self._follow_chat_bottom = value >= self.scroll.verticalScrollBar().maximum() - 2
    def toggle_details(self,index):
        self.details.setCurrentIndex(index);self.details.show()
    def resizeEvent(self,event):
        super().resizeEvent(event)
        self._resize_header_actions()
        self.input_hint.setVisible(self.width()>=500)
        self.body.setDirection(QBoxLayout.LeftToRight)
        self.details.setFixedWidth(min(440,max(220,int(self.width()*0.36))))
        self.details.setMaximumHeight(16777215)
    def _resize_header_actions(self):
        self.header.setDirection(QBoxLayout.LeftToRight)
        available=max(1,self.contentsRect().width()-28)
        tight=available<360 or self.height()<320
        compact=tight or available<500 or self.height()<430
        font_size=11 if tight else (12 if compact else 13)
        gap=4 if compact else 6
        padding=3 if tight else (4 if compact else 6)
        minimum_height=24 if tight else (26 if compact else 28)
        height=(26 if tight else 30) if compact or self.height()<600 else 34
        style_key=(font_size,padding)
        if getattr(self,'_header_style_key',None)!=style_key:
            for button in self.header_buttons:
                button.setStyleSheet(f'font-size:{font_size}px;padding:3px {padding}px;border-radius:6px;')
                button.ensurePolished()
            self.badge.setStyleSheet(f'font-size:{font_size}px;padding:2px {padding}px;')
            self.badge.ensurePolished()
            self._header_style_key=style_key
        self.badge.setMinimumHeight(minimum_height)
        self.badge.setMaximumHeight(height)
        reserve=self.brand.sizeHint().width()+12
        budget=max(1,min(int(available*0.62),available-reserve))
        minimums=[b.fontMetrics().horizontalAdvance(b.text())+padding*2+6+(12 if b is self.history_button else 0)
                  for b in self.header_buttons]
        maximums=[width+(12 if compact else 18) for width in minimums]
        def column_widths(widths,columns):
            return [max(widths[column::columns]) for column in range(columns)]
        columns=next((count for count in (4,2,1)
                      if (count!=4 or available>=580)
                      and sum(column_widths(minimums,count))+gap*(count-1)<=budget),1)
        self.identity.setDirection(QBoxLayout.LeftToRight if columns==4 else QBoxLayout.TopToBottom)
        self.action_grid.setSpacing(gap)
        group_minimum=sum(column_widths(minimums,columns))+gap*(columns-1)
        self.action_bar.setMinimumWidth(group_minimum)
        self.action_bar.setMaximumWidth(max(group_minimum,min(budget,sum(column_widths(maximums,columns))+gap*(columns-1))))
        rows=(len(minimums)+columns-1)//columns
        self.action_bar.setMinimumHeight(rows*minimum_height+gap*(rows-1))
        self.action_bar.setMaximumHeight(rows*height+gap*(rows-1))
        rebuild=getattr(self,'_header_columns',None)!=columns
        if rebuild:
            for column in range(4):
                self.action_grid.setColumnStretch(column,1 if column<columns else 0)
        for index,button in enumerate(self.header_buttons):
            button.setMinimumSize(minimums[index],minimum_height)
            button.setMaximumSize(maximums[index],height)
            button.setSizePolicy(QSizePolicy.Expanding,QSizePolicy.Preferred)
            if rebuild:
                self.action_grid.removeWidget(button)
                self.action_grid.addWidget(button,index//columns,index%columns)
        self._header_columns=columns

    def update_buttons(self):
        busy=self.busy;drafts=bool(self.session.drafts)
        self.send_button.setEnabled(not busy);self.stop_button.setEnabled(busy);self.input.setEnabled(not busy)
        for widget in (self.backend,self.endpoint,self.model,self.mode,self.key,self.steps,self.timeout,self.refresh_button,self.local_button,self.unload_button,self.local_profile,self.idle,self.task_mode,self.new_button,self.history_button,self.import_button,self.import_json_button):widget.setEnabled(not busy)
        self.badge.setEnabled(not busy);self.manage_models_button.setEnabled(not busy);self.update_draft_controls()
        self.write_button.setEnabled(not busy and drafts and not self.written);self.edit_button.setEnabled(not busy and drafts and not self.written);self.export_button.setEnabled(not busy and drafts)
    def send(self):
        text=self.input.toPlainText().strip()
        if not text or self.busy:return
        if len(text)>4000:QMessageBox.warning(self,'内容过长','请将本次需求控制在 4000 字以内。');return
        self.start_worker(text)
    def start_worker(self,text,action='chat'):
        if self.busy:return
        w=self.window;v=w.view_workspace
        if not application_state(w).can_start_execution():
            QMessageBox.warning(self,'暂时无法开始','请先结束任务、录制或指令测试。');return
        try:settings=self.settings();self.save_settings(settings)
        except Exception as error:QMessageBox.warning(self,'模型设置',str(error));return
        if action=='chat':
            if self.written:self.session.drafts=[];self.written=False;self.render_drafts()
            self.add_message('user',text);self.input.clear()
        worker=self.worker=AgentWorker(self.session,text,settings,self,action)
        worker.progress.connect(self.on_event);worker.finished.connect(self.completed);worker.start();self.update_buttons()
    def on_event(self,kind,value):
        if not self._restoring and kind in ('tool_start','tool_result','verification_evidence'):
            self._chat_events.append([kind,deepcopy(value)])
        if kind=='status':self.status.setText(value)
        elif kind in ('assistant','error'):
            self.add_message('assistant',value if kind=='assistant' else '未完成：'+value)
            self.status.setText('本轮完成' if kind=='assistant' else '执行中断 · 可调整后重试')
            if kind=='error' and self.worker is not None and self.worker.action=='local':
                self._model_notice=QMessageBox(QMessageBox.Warning,'本机模型不可用',str(value),QMessageBox.Ok,self)
                self._model_notice.open()
        elif kind=='local_status':self.status.setText(value);self.badge.setText(value)
        elif kind=='models':
            current=self.model.currentText();self.model.clear();self.model.addItems(value);self.model.setEditText(current if current in value or not value else value[0])
            self.status.setText('连接成功 · '+str(len(value))+' 个模型');self.badge.setText('模型已连接')
        elif kind=='verification_evidence':self.add_evidence(value)
        elif kind=='verification_failed':
            self._verification_failure=value;self.status.setText('核验未通过 · 等待是否保留流程')
        elif kind=='drafts':self.render_drafts(value)
        elif kind=='tool_start':
            frame=QFrame();frame.setObjectName('agentTool');layout=QVBoxLayout(frame);layout.setContentsMargins(10,6,10,6)
            button=QToolButton();button.setText('◌ '+value['name']+' · 执行中');button.setCheckable(True);button.setToolButtonStyle(Qt.ToolButtonTextOnly)
            detail=QPlainTextEdit(json.dumps(value,ensure_ascii=False,indent=2));detail.setReadOnly(True);detail.setMaximumHeight(160);detail.hide();button.toggled.connect(detail.setVisible)
            layout.addWidget(button);layout.addWidget(detail);self.message_layout.insertWidget(self.message_layout.count()-1,frame);self._cards.append(frame);self._tool_card=(button,detail);self._trim_cards();self.scroll_bottom()
        elif kind=='tool_result' and self._tool_card:
            if value.get('ok') and isinstance(value.get('result'),dict):
                result=value['result'];evidence=result.get('visual_verification',result)
                if evidence.get('screenshot'):self.add_evidence(evidence)
            button,detail=self._tool_card;button.setText(('✓ ' if value['ok'] else '! ')+value['tool']+(' · 完成' if value['ok'] else ' · 未完成'))
            detail.appendPlainText(json.dumps(value,ensure_ascii=False,indent=2));self._tool_card=None
    def add_evidence(self,evidence):
        # Failed checks and old history may legitimately have no screenshot.
        if not isinstance(evidence,dict):evidence={'error':'核验记录格式无效'}
        raw_path=evidence.get('screenshot')
        path=None
        if isinstance(raw_path,str) and raw_path.strip():
            try:
                candidate=Path(raw_path)
                if candidate.is_file():path=candidate
            except (OSError,ValueError):pass
        frame=QFrame();frame.setObjectName('agentTool');layout=QVBoxLayout(frame)
        structured=evidence.get('method') in ('browser_state','form_state','workbook_state')
        title=('实际状态核验：'+('通过' if evidence.get('verified') else '未通过')) if structured else ('截图 OCR 文字匹配：'+('已匹配（模型另行判断）' if evidence.get('verified') else '未确认'))
        label=QLabel(title);layout.addWidget(label)
        pixmap=QPixmap(str(path)) if path else QPixmap()
        if not pixmap.isNull():
            preview=QLabel();preview.setMinimumWidth(0);preview.setSizePolicy(QSizePolicy.Ignored,QSizePolicy.Preferred);scaled=pixmap.scaled(480,260,Qt.KeepAspectRatio,Qt.SmoothTransformation);preview.setPixmap(scaled);preview.setFixedHeight(scaled.height());preview.setAlignment(Qt.AlignLeft|Qt.AlignTop);layout.addWidget(preview)
            button=QPushButton('打开原始截图');button.clicked.connect(lambda:open_path(str(path)));layout.addWidget(button)
        elif not structured:
            layout.addWidget(QLabel('截图不可用（未生成、已移除或无法读取）'))
        missing=evidence.get('missing') or []
        missing=', '.join(str(item) for item in missing) if isinstance(missing,(list,tuple)) else str(missing)
        detail=QPlainTextEdit(str(evidence.get('text') or '')+'\n未匹配：'+missing+'\n'+str(evidence.get('error') or ''));detail.setReadOnly(True);detail.setMaximumHeight(100);layout.addWidget(detail)
        layout.setSizeConstraint(QLayout.SetMinimumSize);frame.setMinimumHeight(layout.sizeHint().height())
        self.message_layout.insertWidget(self.message_layout.count()-1,frame);self._cards.append(frame);self._trim_cards();self.scroll_bottom()
    def completed(self):
        worker=self.worker;worker.wait();self.worker=None
        worker.deleteLater();self.render_drafts();self.update_buttons();self.scroll_bottom()
        if self._tool_card:
            self._tool_card[0].setText('已中断 · 请重新查看结果');self._tool_card=None
        failure=getattr(self,'_verification_failure',None)
        if failure:
            self._verification_failure=None
            self.confirm_failed_verification(failure)
        self._save_history()
    def confirm_failed_verification(self,failure):
        dialog=QMessageBox(QMessageBox.Warning,'任务结果核验未通过',failure['reason']+'\n\n已试运行 '+str(failure.get('executed',0))+' 个步骤，产生的操作不会撤销。\n是否将核验失败流程加入草稿？',QMessageBox.Yes|QMessageBox.No,self)
        dialog.setDefaultButton(QMessageBox.No)
        dialog.button(QMessageBox.Yes).setText('仍加入草稿')
        dialog.button(QMessageBox.No).setText('不加入')
        dialog.setDetailedText(json.dumps(failure['instructions'],ensure_ascii=False,indent=2))
        accept=dialog.exec()==QMessageBox.Yes
        try:
            self.session.resolve_verification(failure['id'],accept,ExecutionContext())
            self.render_drafts();self.update_buttons()
            self.add_message('assistant','已按你的选择加入草稿，标记为核验失败；加入草稿没有再次执行。' if accept else '核验失败流程未加入草稿。')
        except Exception as error:QMessageBox.warning(self,'草稿处理失败',str(error))
    def stop(self):
        if self.worker:self.worker.context.stop_requested=True;self.status.setText('正在停止…');self.stop_button.setEnabled(False)
    def render_drafts(self,snapshot=None):
        drafts=self.session.drafts if snapshot is None else [InstructionDraft.from_mapping(d) for d in snapshot]
        self.preview.setRowCount(len(drafts));self.drafts_button.setText(f'草稿 {len(drafts)}')
        self._resize_header_actions()
        self.preview.setVisible(bool(drafts));self.empty_drafts.setVisible(not drafts)
        for row,draft in enumerate(drafts):
            self.preview.setItem(row,0,QTableWidgetItem(draft.type_id));self.preview.setItem(row,1,QTableWidgetItem(json.dumps(draft.parameters,ensure_ascii=False)))
        if drafts:self.details.setCurrentIndex(0);self.details.show()
        if hasattr(self,'history_timer') and not self.busy and not self._restoring:self.history_timer.start()
    def draft_context_menu(self,position):
        index=self.preview.indexAt(position)
        if not index.isValid():return
        self.preview.selectRow(index.row());self.update_draft_controls()
        menu=QMenu(self.preview)
        for title,button,callback in (
            ('删除',self.delete_draft_button,self.delete_draft),
            ('上移',self.move_up_button,lambda:self.move_draft(-1)),
            ('下移',self.move_down_button,lambda:self.move_draft(1))):
            action=menu.addAction(title);action.setEnabled(button.isEnabled());action.triggered.connect(callback)
        try:menu.exec(self.preview.viewport().mapToGlobal(position))
        finally:menu.deleteLater()
    def update_draft_controls(self):
        if not hasattr(self,'delete_draft_button'):return
        row=self.preview.currentRow();count=len(self.session.drafts)
        editable=not self.busy and not self.written and 0<=row<count
        self.delete_draft_button.setEnabled(editable)
        self.move_up_button.setEnabled(editable and row>0)
        self.move_down_button.setEnabled(editable and row<count-1)
    def delete_draft(self):
        row=self.preview.currentRow()
        if self.busy or self.written or not 0<=row<len(self.session.drafts):return
        del self.session.drafts[row]
        self.render_drafts()
        if self.session.drafts:self.preview.selectRow(min(row,len(self.session.drafts)-1))
        self.update_buttons();self._save_history();self.status.setText('已删除选中的草稿步骤')
    def move_draft(self,offset):
        row=self.preview.currentRow();target=row+offset
        if self.busy or self.written or offset not in (-1,1) or not (0<=row<len(self.session.drafts) and 0<=target<len(self.session.drafts)):return
        drafts=self.session.drafts;drafts[row],drafts[target]=drafts[target],drafts[row]
        self.render_drafts();self.preview.selectRow(target);self.update_buttons();self._save_history()
        self.status.setText('已调整草稿顺序，写入和导出将使用此顺序')
    def edit_draft(self):
        if self.busy or self.written:return
        row=self.preview.currentRow()
        if row<0:return
        draft=self.session.drafts[row];editor=get_instruction_spec(draft.type_id).create_editor(parent=self,draft=draft)
        try:
            if editor.exec()==QDialog.Accepted:self.session.drafts[row]=editor.get_draft();self.render_drafts()
        finally:editor.deleteLater()
    def write(self):
        if self.busy or self.written or not self.session.drafts:return
        if not application_state(self.window).can_edit_project():return
        try:
            validated=[]
            for i,draft in enumerate(self.session.drafts):
                editor=get_instruction_spec(draft.type_id).create_editor(parent=self,draft=draft)
                try:validated.append(editor.get_draft())
                except Exception as error:raise ValueError(f'第 {i+1} 行：{error}') from error
                finally:editor.deleteLater()
            controls=any(d.type_id in ('循环','条件循环','条件判断','报错跳转','变量比较','暂不运行以下指令','暂不运行以上指令','终止流程','运行项目') for d in validated)
            workspace=self.window.workspace;ids=workspace.repository.append_recording(validated,connect=not controls)
            self.written=True;self._save_history();workspace.reload_graph();workspace.graphFinalized.emit(False);self.update_buttons()
            self.status.setText(f'已写入 {len(ids)} 条指令'+(' · 包含流程控制，请在流程图连接分支' if controls else ' · 已同步表格和流程图'))
        except Exception as error:QMessageBox.warning(self,'请检查草稿',str(error))
    def export(self):
        path,_=QFileDialog.getSaveFileName(self,'导出指令草稿','anclicker-agent.json','JSON (*.json)')
        if path:
            try:
                Path = _module_imports.load('Path')
                Path(path).write_text(json.dumps(export_drafts(self.session.drafts),ensure_ascii=False,indent=2),encoding='utf-8')
            except OSError as error:QMessageBox.warning(self,'导出失败',str(error))
    def import_json(self):
        if self.busy:return
        path,_=QFileDialog.getOpenFileName(self,'导入 API 草稿','','JSON (*.json)')
        if not path:return
        try:
            Path = _module_imports.load('Path')
            source=Path(path)
            if source.stat().st_size>2_000_000:raise ValueError('草稿文件过大')
            payload=json.loads(source.read_text(encoding='utf-8'))
            if payload.get('protocol')!='anclicker.agent.v1' or payload.get('kind')!='instruction_drafts':raise ValueError('不是 AnClicker 标准草稿文件')
            items=payload.get('instructions')
            if not isinstance(items,list) or not items:raise ValueError('草稿为空或格式无效')
            if len(items)+(0 if self.written else len(self.session.drafts))>100:raise ValueError('草稿最多 100 行')
            drafts=[]
            for item in items:
                draft=InstructionDraft.from_mapping(item)
                validated=make_draft(draft.type_id,draft.parameters,draft.repeat_count,draft.note)
                validated.error_policy=draft.error_policy;drafts.append(validated)
            if self.written:self.session.drafts=[];self.written=False
            self.session.drafts.extend(drafts);self.render_drafts();self.update_buttons()
            self.status.setText(f'已导入 {len(drafts)} 条可编辑草稿，尚未执行')
        except Exception as error:QMessageBox.warning(self,'导入失败',str(error))
    def import_recording(self):
        page=self.window.view_workspace.web_recording_page
        if self.busy or page.busy:return
        if not page.drafts:self.status.setText('网页录制中还没有可导入的草稿');return
        if self.written:self.session.drafts=[];self.written=False
        self.session.drafts.extend(deepcopy(page.drafts));self.render_drafts();self.update_buttons();self.status.setText('已导入网页录制草稿，可继续对话修改')
    def _load_history(self):
        try:
            data=json.loads(self.window.db.get_setting_value('对话Agent历史') or '[]')
            if not isinstance(data,list):return
            for entry in data:
                if not isinstance(entry,dict) or not isinstance(entry.get('id'),str):continue
                if not isinstance(entry.get('events'),list) or not isinstance(entry.get('drafts'),list):continue
                try:
                    for draft in entry['drafts']:InstructionDraft.from_mapping(draft)
                    for kind,value in entry['events']:
                        if not isinstance(value,dict):raise ValueError('历史事件格式无效')
                        if kind=='message' and (value.get('role') not in ('user','assistant') or not isinstance(value.get('text'),str)):raise ValueError('历史消息格式无效')
                except (TypeError,ValueError,KeyError):continue
                self._history.append(entry)
                if len(self._history)==20:break
        except (ValueError,TypeError,AttributeError):
            self._history=[]
    def _save_history(self):
        if self._restoring or self.busy:return True
        users=[event[1]['text'] for event in self._chat_events if event[0]=='message' and event[1]['role']=='user']
        if not users and not self.session.drafts and not self.input.toPlainText().strip():return True
        entry={'id':self._chat_id,'title':(users[0] if users else self.input.toPlainText().strip() or '指令草稿')[:40],
               'updated':datetime.now().strftime('%m-%d %H:%M'),'events':deepcopy(self._chat_events),
               'drafts':[draft_data(d) for d in self.session.drafts],'written':self.written,
               'input':self.input.toPlainText(),'history':deepcopy(getattr(self.session,'history',[])),
               'pending_plan_text':getattr(self.session,'pending_plan_text',''),
               'pending_sheet_target':getattr(self.session,'pending_sheet_target',None)}
        history=[entry]+[item for item in self._history if item['id']!=self._chat_id]
        try:
            self.window.db.set_setting_value('对话Agent历史',json.dumps(history[:20],ensure_ascii=False))
        except Exception as error:
            self.status.setText('历史对话保存失败：'+str(error));return False
        self._history=history[:20]
        return True
    def _refresh_history_menu(self):
        self._save_history();self.history_menu.clear()
        if not self._history:
            self.history_menu.addAction('暂无历史对话').setEnabled(False);return
        self.history_menu.setMaximumHeight(min(480,self.screen().availableGeometry().height()-80))
        for item in self._history:
            full_title=' '.join(str(item.get('title','未命名对话')).split())
            title=self.history_menu.fontMetrics().elidedText(full_title,Qt.ElideRight,min(240,max(110,self.width()-220))).replace('&','&&')
            action=self.history_menu.addAction(f"{title}   · {len(item['drafts'])} 条草稿")
            action.setToolTip(item.get('updated','')+'  '+full_title+('（当前对话）' if item['id']==self._chat_id else ''))
            action.setData(item['id']);action.setCheckable(True);action.setChecked(item['id']==self._chat_id)
            action.triggered.connect(lambda checked=False,key=item['id']:self._restore_chat(key))
    def history_context_menu(self,position):
        item=self.history_menu.actionAt(position)
        if item is None or not item.data():return
        key=item.data();menu=QMenu(self.history_menu)
        action=menu.addAction('删除');action.setEnabled(not self.busy)
        action.triggered.connect(lambda:self.delete_history(key))
        try:menu.exec(self.history_menu.mapToGlobal(position))
        finally:menu.deleteLater()
    def delete_history(self,key):
        if self.busy:return
        entry=next((item for item in self._history if item['id']==key),None)
        if entry is None:return
        self.history_menu.hide()
        if QMessageBox.question(self,'删除历史对话','删除“'+str(entry.get('title','未命名对话'))+'”及其对应草稿？已写入项目的指令不会删除。',QMessageBox.Yes|QMessageBox.No,QMessageBox.No)!=QMessageBox.Yes:return
        history=[item for item in self._history if item['id']!=key]
        try:self.window.db.set_setting_value('对话Agent历史',json.dumps(history,ensure_ascii=False))
        except Exception as error:QMessageBox.warning(self,'删除失败',str(error));return
        self._history=history
        if key==self._chat_id:
            self.history_timer.stop();self.session.close();self.session=create_agent_session()
            self._chat_id=uuid4().hex;self._chat_events=[];self._verification_failure=None;self.written=False
            self._clear_chat_cards();self.input.clear();self.render_drafts();self.welcome();self.update_buttons()
        self._refresh_history_menu();self.status.setText('已删除历史对话及对应草稿')
    def _clear_chat_cards(self):
        for card in self._cards:self.message_layout.removeWidget(card);card.hide();card.deleteLater()
        self._cards=[];self._tool_card=None
    def _restore_chat(self,key,save_current=True):
        if self.busy:return
        entry=next((deepcopy(item) for item in self._history if item['id']==key),None)
        if entry is None:return
        if save_current and key==self._chat_id:return
        if save_current and not self._save_history():return
        self.history_timer.stop()
        self.session.close();self.session=create_agent_session()
        self._restoring=True
        try:
            self._chat_id=entry['id'];self._chat_events=deepcopy(entry['events'])
            self.session.drafts=[InstructionDraft.from_mapping(d) for d in entry['drafts']]
            if hasattr(self.session,'history'):self.session.history=deepcopy(entry.get('history',[]))
            if hasattr(self.session,'pending_plan_text'):self.session.pending_plan_text=entry.get('pending_plan_text','')
            self.session.pending_sheet_target=entry.get('pending_sheet_target') if isinstance(entry.get('pending_sheet_target'),dict) else None
            self.written=bool(entry.get('written',False));self._verification_failure=None
            self._clear_chat_cards()
            for kind,value in self._chat_events:
                if kind=='message':self.add_message(value['role'],value['text'])
                elif kind in ('tool_start','tool_result','verification_evidence'):self.on_event(kind,value)
            if self._tool_card:self._tool_card[0].setText('历史操作 · 未完成');self._tool_card=None
            self.input.setPlainText(entry.get('input',''));self.render_drafts();self.update_buttons()
            self.status.setText('已恢复历史对话与草稿 · 可继续对话')
        finally:
            self._restoring=False
        self._save_history()
    def new_chat(self):
        if self.busy or not self._save_history():return
        self.history_timer.stop()
        self.session.close();self.session=create_agent_session();self.written=False
        self._chat_id=uuid4().hex;self._chat_events=[];self._verification_failure=None
        self._clear_chat_cards();self.input.clear();self.render_drafts();self.details.setCurrentIndex(1);self.details.show();self.welcome();self.update_buttons();self.status.setText('新对话 · 上次对话与草稿已保存')
    def start_local(self):
        self.backend.setCurrentIndex(0);self.endpoint.setText('http://127.0.0.1:8766/v1');self.model.setEditText('anclicker-small');self.mode.setCurrentIndex(0)
        self.status.setText('正在检测资源并启动模型…');self.start_worker('',action='local')
    def manage_local_models(self):
        if self.busy:return
        LocalModelDialog=_module_imports.load('LocalModelDialog')
        dialog=LocalModelDialog(self)
        try:
            dialog.exec()
            if dialog.activate:self.start_local()
            elif dialog.changed:self.refresh_resources()
        finally:dialog.deleteLater()
    def refresh_resources(self):
        if self.backend.currentData()!='compatible' or self.endpoint.text().rstrip('/')!='http://127.0.0.1:8766/v1':return
        local_snapshot = _module_imports.load('local_snapshot')
        try:snapshot=local_snapshot()
        except (ValueError,RuntimeError):return
        status=snapshot['status']
        if status=='模型尚未启动':return
        label=('GPU' if status.startswith('GPU') else 'CPU') if '已就绪' in status else ('已释放 · 按需唤醒' if '释放' in status or '已停止' in status else '模型加载中' if '加载' in status else status)
        self.badge.setText(('双模型 · ' if snapshot.get('dual') else '')+label+((' · RAM '+str(snapshot['memory_mb'])+' MB') if snapshot['memory_mb'] else ''))
        self.badge.setToolTip((snapshot.get('model','')+'；' if snapshot.get('model') else '')+status+'；空闲 '+str(snapshot['idle_seconds'])+' 秒后释放；点击切换、新增或删除模型')
    def stop_local(self):
        stop_local_model = _module_imports.load('stop_local_model')
        try:stop_local_model();self.status.setText('已释放本机模型，下次消息自动唤醒');self.refresh_resources()
        except RuntimeError as error:QMessageBox.information(self,'模型正在使用',str(error))
    def shutdown(self):
        if self.busy:raise RuntimeError('请先停止对话Ai编程')
        self._save_history()
        self.session.close()
        stop_local_model = _module_imports.load('stop_local_model')
        try:stop_local_model(adopt=False)
        except RuntimeError:pass  # Another app window is still using the shared model.
    def apply_theme(self,mode):
        self._theme_mode=mode
        light=mode=='light'
        bg,surface,ink,dim,line,accent=('#f7f7f8','#ffffff','#202535','#7a8194','#e3e6ef','#6c5ce7') if light else ('#09090b','#1d202a','#e9ecf5','#8c94a8','#303644','#9d92ff')
        self.scroll.viewport().setStyleSheet(f'background:{bg};')
        self.messages.setObjectName('agentMessages');self.messages.setStyleSheet(f'QWidget#agentMessages {{background:{bg};}}')
        self.setStyleSheet(f'''QWidget#agentPage {{background:{bg}; color:{ink};font-family:'Microsoft YaHei UI';font-size:13px;}}
        QWidget#agentPage QLabel {{color:{ink};background:transparent;}}
        QWidget#agentDraftPage {{background:{surface};}}
        QWidget#agentPage QTableWidget {{background:{bg};alternate-background-color:{surface};color:{ink};border:1px solid {line};border-radius:8px;selection-background-color:{accent};selection-color:{'#ffffff' if light else '#191528'};}}
        QWidget#agentPage QTableWidget::item {{padding:6px;border:0;}}
        QWidget#agentPage QTableWidget::item:selected {{background:{accent};color:{'#ffffff' if light else '#191528'};}}
        QWidget#agentPage QHeaderView::section {{background:{surface};color:{dim};border:0;border-bottom:1px solid {line};padding:8px;text-align:left;}}
        QWidget#agentPage QPlainTextEdit {{background:{bg};color:{ink};border:1px solid {line};border-radius:8px;padding:6px;selection-background-color:{accent};}}
        QWidget#agentPage QToolButton {{background:transparent;color:{ink};border:0;padding:6px;}}
        QWidget#agentPage QPushButton:hover {{border-color:{accent};}}
        QWidget#agentPage QPushButton:focus {{border:1px solid {accent};}}
        QWidget#agentPage QScrollBar:vertical {{background:transparent;width:8px;margin:0;}}
        QWidget#agentPage QScrollBar::handle:vertical {{background:{line};min-height:24px;border-radius:4px;}}
        QWidget#agentPage QScrollBar::add-line:vertical,QWidget#agentPage QScrollBar::sub-line:vertical {{height:0;}}
        QWidget#agentPage QScrollBar::add-page:vertical,QWidget#agentPage QScrollBar::sub-page:vertical {{background:transparent;}}
        QLabel#agentEmptyState {{color:{dim};padding:22px 8px;}}
        QScrollArea#agentDraftScroll,QScrollArea#agentDraftScroll > QWidget > QWidget,QScrollArea#agentSettingsScroll,QScrollArea#agentSettingsScroll > QWidget > QWidget {{background:{surface};border:0;}}
        QWidget#agentSettingsPage {{background:{surface};color:{ink};}}
        QWidget#agentSettingsPage QLabel {{background:transparent;color:{ink};}}
        QWidget#agentSettingsPage QLineEdit,QWidget#agentSettingsPage QComboBox,QWidget#agentSettingsPage QSpinBox {{background:{bg};color:{ink};border:1px solid {line};border-radius:6px;padding:6px;min-height:22px;selection-background-color:{accent};selection-color:{'#ffffff' if light else '#191528'};}}
        QWidget#agentSettingsPage QComboBox QAbstractItemView {{background:{surface};color:{ink};selection-background-color:{accent};}}
        QWidget#agentPage QTabBar::tab {{background:{surface};color:{ink};border:1px solid {line};padding:6px 10px;}}
        QWidget#agentPage QTabBar::tab:selected {{background:{accent};color:{'#ffffff' if light else '#191528'};}}
        QWidget#agentPage QTabWidget::pane {{background:{surface};border:1px solid {line};}}
        QWidget#agentPage QPushButton {{padding:7px 12px;border-radius:9px;border:1px solid {line};background:{surface};color:{ink};}}
        QWidget#agentPage QPushButton#accentButton {{background:{accent};color:{'#ffffff' if light else '#191528'};font-weight:600;}}
        QMenu {{background:{surface};color:{ink};border:1px solid {line};padding:6px;menu-scrollable:1;font-family:'Microsoft YaHei UI';font-size:13px;}}
        QMenu::item {{padding:10px 16px 10px 24px;border-radius:6px;}}
        QMenu::item:selected {{background:{accent};color:{'#ffffff' if light else '#191528'};}}
        QWidget#agentPage QPushButton:disabled {{color:{dim};}}
        QLabel#agentBrand {{font-size:20px;font-weight:700;color:{ink};}}
        QPushButton#agentBadge {{color:{accent};background:{surface};border:1px solid {line};border-radius:10px;padding:4px 10px;}}
        QLabel#agentHint,QLabel#agentStatus {{color:{dim};font-size:11px;}}
        QFrame#agentAssistant,QFrame#agentComposer,QFrame#agentTool {{background:{surface};border:1px solid {line};border-radius:14px;}}
        QFrame#agentUser {{background:{'#ece9ff' if light else '#30294b'};border:1px solid {line};border-radius:14px;}}
        QFrame#agentAssistant QLabel,QFrame#agentUser QLabel {{background:transparent;border:0;color:{ink};}}
        QFrame#agentComposer QPlainTextEdit {{background:transparent;border:0;color:{ink};font-size:14px;}}
        QPushButton#agentSuggestion {{text-align:left;padding:12px;border-radius:10px;background:{surface};border:1px solid {line};color:{ink};}}
        QLabel#agentSection {{font-size:18px;font-weight:600;}}
        ''')
