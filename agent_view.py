"""Responsive, conversation-first local Agent page."""
import json
from dataclasses import asdict
from copy import deepcopy
from qt_compat.QtCore import Qt, QThread, Signal, QTimer
from qt_compat.QtWidgets import (QWidget,QFrame,QVBoxLayout,QHBoxLayout,QBoxLayout,QLabel,
    QPushButton,QToolButton,QPlainTextEdit,QLineEdit,QComboBox,QSpinBox,QFormLayout,
    QScrollArea,QSizePolicy,QTabWidget,QTableWidget,QTableWidgetItem,QHeaderView,
    QAbstractItemView,QMessageBox,QFileDialog,QDialog)
from instructions.models import ExecutionContext, InstructionDraft
from instructions.registry import get_instruction_spec
from agent_protocol import draft_data, export_drafts, make_draft
from agent_provider import AgentSettings, ModelClient
from agent_factory import create_agent_session

class AgentWorker(QThread):
    progress=Signal(str,object)
    def __init__(self,session,text,settings,parent,action='chat'):
        super().__init__(parent)
        self.session,self.text,self.settings,self.action=session,text,settings,action
        self.context=ExecutionContext();self.error=None
    def run(self):
        try:
            if self.action=='local':
                from agent_local import start_local_model
                self.progress.emit('local_status',start_local_model(self.settings.local_profile,self.context,self.settings.idle_seconds))
            elif self.action=='models':self.progress.emit('models',ModelClient(self.settings).models(self.context))
            else:self.session.run(self.text,self.settings,self.context,self.progress.emit)
        except InterruptedError:self.progress.emit('status','已停止 · 已完成的步骤和草稿保留')
        except Exception as error:
            self.error=str(error);self.progress.emit('error',self.error)

class Composer(QPlainTextEdit):
    submitted=Signal()
    def keyPressEvent(self,event):
        if event.key() in (Qt.Key_Return,Qt.Key_Enter) and not (event.modifiers() & Qt.ShiftModifier):
            self.submitted.emit();event.accept();return
        super().keyPressEvent(event)

class AgentView(QWidget):
    def __init__(self,window):
        super().__init__(window)
        self.window=window;self.session=create_agent_session();self.worker=None;self.written=False
        self.setObjectName('agentPage');self.setAttribute(Qt.WA_StyledBackground,True);self._cards=[];self._tool_card=None
        root=QVBoxLayout(self);root.setContentsMargins(14,12,14,12);root.setSpacing(12)
        header=self.header=QBoxLayout(QBoxLayout.LeftToRight)
        identity=QHBoxLayout();actions=QHBoxLayout()
        header.addLayout(identity,1);header.addLayout(actions)
        brand=QLabel('✦  AnClicker');brand.setObjectName('agentBrand');identity.addWidget(brand)
        self.badge=QLabel('本机小模型');self.badge.setObjectName('agentBadge');identity.addWidget(self.badge);identity.addStretch()
        self.new_button=QPushButton('新对话');self.drafts_button=QPushButton('草稿 0');self.settings_button=QPushButton('设置')
        for b in (self.new_button,self.drafts_button,self.settings_button):actions.addWidget(b)
        root.addLayout(header)
        self.body=QBoxLayout(QBoxLayout.LeftToRight);self.body.setSpacing(12);root.addLayout(self.body,1)
        self.chat=QWidget();self.chat.setMinimumWidth(0);chat=QVBoxLayout(self.chat);chat.setContentsMargins(0,0,0,0);chat.setSpacing(10)
        self.body.addWidget(self.chat,1)
        self.scroll=QScrollArea();self.scroll.setWidgetResizable(True);self.scroll.setFrameShape(QFrame.NoFrame)
        self.scroll.setHorizontalScrollBarPolicy(Qt.ScrollBarAlwaysOff)
        self.messages=QWidget();self.message_layout=QVBoxLayout(self.messages);self.message_layout.setContentsMargins(2,8,2,8);self.message_layout.setSpacing(14)
        self.message_layout.addStretch();self.scroll.setWidget(self.messages);chat.addWidget(self.scroll,1)
        self.status=QLabel('准备就绪 · 私有 API 模式' if hasattr(self.session,'api_url') else '准备就绪 · 模型按需运行');self.status.setObjectName('agentStatus');self.status.setWordWrap(True);chat.addWidget(self.status)
        composer=QFrame();composer.setObjectName('agentComposer');box=QVBoxLayout(composer);box.setContentsMargins(12,8,12,8)
        self.input=Composer();self.input.setPlaceholderText('说说你想完成的事…');self.input.setFixedHeight(66);self.input.setFrameShape(QFrame.NoFrame);box.addWidget(self.input)
        bottom=QHBoxLayout();hint=self.input_hint=QLabel('Enter 发送 · Shift + Enter 换行');hint.setObjectName('agentHint');bottom.addWidget(hint);bottom.addStretch()
        self.stop_button=QPushButton('停止');self.send_button=QPushButton('发送 ↑');self.send_button.setObjectName('accentButton')
        bottom.addWidget(self.stop_button);bottom.addWidget(self.send_button);box.addLayout(bottom);chat.addWidget(composer)
        self.details=QTabWidget();self.details.setMinimumWidth(0);self.details.setMaximumWidth(440);self.body.addWidget(self.details)
        self._build_drafts();self._build_settings();self.details.hide()
        self.new_button.clicked.connect(self.new_chat);self.drafts_button.clicked.connect(lambda:self.toggle_details(0));self.settings_button.clicked.connect(lambda:self.toggle_details(1))
        self.send_button.clicked.connect(self.send);self.input.submitted.connect(self.send);self.stop_button.clicked.connect(self.stop)
        self._load_settings();self.welcome();self.update_buttons();self.apply_theme('dark')
        self.resource_timer=QTimer(self);self.resource_timer.setInterval(2000);self.resource_timer.timeout.connect(self.refresh_resources);self.resource_timer.start()
    @property
    def busy(self):return self.worker is not None
    @property
    def unsaved(self):return bool(self.session.drafts and not self.written)
    def _build_drafts(self):
        page=QWidget();layout=QVBoxLayout(page)
        title=QLabel('指令草稿');title.setObjectName('agentSection');layout.addWidget(title)
        hint=QLabel('对话生成的指令先保留在这里。双击可用原有设置窗口修改。');hint.setWordWrap(True);layout.addWidget(hint)
        self.preview=QTableWidget(0,2);self.preview.setHorizontalHeaderLabels(['指令','参数'])
        self.preview.setSelectionBehavior(QAbstractItemView.SelectRows);self.preview.setEditTriggers(QAbstractItemView.NoEditTriggers)
        self.preview.horizontalHeader().setSectionResizeMode(1,QHeaderView.Stretch);self.preview.setMinimumWidth(0);layout.addWidget(self.preview,1)
        self.edit_button=QPushButton('编辑选中指令');self.write_button=QPushButton('写入表格与流程图');self.write_button.setObjectName('accentButton')
        self.export_button=QPushButton('导出标准 JSON');self.import_button=QPushButton('导入网页录制草稿')
        for b in (self.edit_button,self.write_button,self.export_button,self.import_button):layout.addWidget(b)
        self.draft_hint=QLabel('写入后可在流程图检查连线，再运行任务。');self.draft_hint.setWordWrap(True);layout.addWidget(self.draft_hint)
        self.details.addTab(page,'草稿')
        self.preview.cellDoubleClicked.connect(lambda *_:self.edit_draft());self.edit_button.clicked.connect(self.edit_draft)
        self.write_button.clicked.connect(self.write);self.export_button.clicked.connect(self.export);self.import_button.clicked.connect(self.import_recording)
    def _build_settings(self):
        scroll=QScrollArea();scroll.setWidgetResizable(True);scroll.setFrameShape(QFrame.NoFrame)
        page=QWidget();form=QFormLayout(page);form.setFieldGrowthPolicy(QFormLayout.AllNonFixedFieldsGrow);form.setRowWrapPolicy(QFormLayout.WrapAllRows)
        self.backend=QComboBox();self.backend.addItem('本地 / OpenAI 兼容','compatible');self.backend.addItem('Ollama','ollama')
        self.endpoint=QLineEdit();self.model=QComboBox();self.model.setEditable(True)
        self.mode=QComboBox();self.mode.addItem('标准 JSON · 小模型','json');self.mode.addItem('原生工具调用','native')
        self.key=QLineEdit();self.key.setEchoMode(QLineEdit.Password);self.key.setPlaceholderText('可选，仅本次会话保留')
        self.steps=QSpinBox();self.steps.setRange(1,30);self.timeout=QSpinBox();self.timeout.setRange(10,300);self.timeout.setSuffix(' 秒')
        for label,widget in [('服务类型',self.backend),('服务地址',self.endpoint),('模型名称',self.model),('调用格式',self.mode),('API Key',self.key),('每轮最多步骤',self.steps),('请求超时',self.timeout)]:form.addRow(label,widget)
        self.local_profile=QComboBox()
        for title,value in [('自动调度','auto'),('优先 CPU · 低占用','cpu'),('优先 GPU · 失败回退 CPU','gpu')]:self.local_profile.addItem(title,value)
        self.idle=QSpinBox();self.idle.setRange(30,3600);self.idle.setSuffix(' 秒')
        form.addRow('本机计算资源',self.local_profile);form.addRow('空闲后释放模型',self.idle)
        self.refresh_button=QPushButton('检测连接 / 获取模型');form.addRow(self.refresh_button)
        self.local_button=QPushButton('启动已准备的本机模型');form.addRow(self.local_button)
        self.unload_button=QPushButton('释放本机模型');form.addRow(self.unload_button)
        self.unload_button.clicked.connect(self.stop_local)
        self.model_note=QLabel('429 MB 中文小模型。发送消息时按需启动；低内存优先尝试可用显卡，失败回退 CPU。单任务排队，空闲自动释放。其他电脑先准备运行器和模型。');self.model_note.setWordWrap(True);form.addRow(self.model_note)
        self.refresh_button.clicked.connect(lambda:self.start_worker('',action='models'));self.local_button.clicked.connect(self.start_local)
        scroll.setWidget(page);self.details.addTab(scroll,'模型设置')
    def _load_settings(self):
        settings=asdict(AgentSettings())
        try:
            saved=json.loads(self.window.db.get_setting_value('对话Agent设置') or '{}')
            settings.update({k:v for k,v in saved.items() if k in settings and k!='api_key'})
            AgentSettings(**settings).validate()
        except (ValueError,TypeError,AttributeError):settings=asdict(AgentSettings())
        self.backend.setCurrentIndex(max(0,self.backend.findData(settings['backend'])));self.endpoint.setText(str(settings['endpoint']));self.model.setEditText(str(settings['model']))
        self.mode.setCurrentIndex(max(0,self.mode.findData(settings['mode'])));self.steps.setValue(int(settings['max_steps']));self.timeout.setValue(int(settings['timeout']));self.local_profile.setCurrentIndex(max(0,self.local_profile.findData(settings['local_profile'])));self.idle.setValue(int(settings['idle_seconds']))
    def settings(self):
        return AgentSettings(self.backend.currentData(),self.endpoint.text().strip(),self.model.currentText().strip(),self.mode.currentData(),self.steps.value(),self.timeout.value(),self.key.text().strip(),self.local_profile.currentData(),self.idle.value()).validate()
    def save_settings(self,settings):
        data=asdict(settings);data.pop('api_key',None)
        self.window.db.set_setting_value('对话Agent设置',json.dumps(data,ensure_ascii=False))
    def welcome(self):
        self.add_message('assistant','把想做的事，告诉我。\n\n我可以打开网页、点击和填写内容，也可以帮你编写 AnClicker 指令。')
        frame=QFrame();layout=QVBoxLayout(frame);layout.setContentsMargins(8,0,8,8)
        for text in ('编写一条等待 2 秒的指令','打开 https://example.com 并查看页面','帮我查找图像点击有哪些参数'):
            b=QPushButton(text+'  ↗');b.setObjectName('agentSuggestion');b.setSizePolicy(QSizePolicy.Ignored,QSizePolicy.Fixed);b.clicked.connect(lambda _=False,t=text:self.input.setPlainText(t));layout.addWidget(b)
        self.message_layout.insertWidget(self.message_layout.count()-1,frame);self._cards.append(frame)
    def add_message(self,role,text):
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
    def scroll_bottom(self):QTimer.singleShot(0,lambda:self.scroll.verticalScrollBar().setValue(self.scroll.verticalScrollBar().maximum()))
    def toggle_details(self,index):
        if self.details.isVisible() and self.details.currentIndex()==index:self.details.hide()
        else:self.details.setCurrentIndex(index);self.details.show()
    def resizeEvent(self,event):
        super().resizeEvent(event)
        narrow=self.width()<760
        self.header.setDirection(QBoxLayout.TopToBottom if self.width()<600 else QBoxLayout.LeftToRight)
        self.input_hint.setVisible(self.width()>=500)
        self.body.setDirection(QBoxLayout.TopToBottom if narrow else QBoxLayout.LeftToRight)
        self.details.setMaximumWidth(16777215 if narrow else 440)
        self.details.setMaximumHeight(280 if narrow else 16777215)
    def update_buttons(self):
        busy=self.busy;drafts=bool(self.session.drafts)
        self.send_button.setEnabled(not busy);self.stop_button.setEnabled(busy);self.input.setEnabled(not busy)
        for widget in (self.backend,self.endpoint,self.model,self.mode,self.key,self.steps,self.timeout,self.refresh_button,self.local_button,self.unload_button,self.local_profile,self.idle,self.new_button,self.import_button):widget.setEnabled(not busy)
        self.write_button.setEnabled(not busy and drafts and not self.written);self.edit_button.setEnabled(not busy and drafts and not self.written);self.export_button.setEnabled(not busy and drafts)
    def send(self):
        text=self.input.toPlainText().strip()
        if not text or self.busy:return
        if len(text)>4000:QMessageBox.warning(self,'内容过长','请将本次需求控制在 4000 字以内。');return
        self.start_worker(text)
    def start_worker(self,text,action='chat'):
        if self.busy:return
        w=self.window;v=w.view_workspace
        if w.command_thread.isRunning() or getattr(getattr(w,'task_scheduler',None),'busy',False) or v.recording_page.busy or v.web_recording_page.busy or getattr(w.workspace,'_instruction_test_active',False) or getattr(w,'_update_preparing',False):
            QMessageBox.warning(self,'暂时无法开始','请先结束任务、录制或指令测试。');return
        try:settings=self.settings();self.save_settings(settings)
        except Exception as error:QMessageBox.warning(self,'模型设置',str(error));return
        if action=='chat':
            if self.written:self.session.drafts=[];self.written=False;self.render_drafts()
            self.add_message('user',text);self.input.clear()
        worker=self.worker=AgentWorker(self.session,text,settings,self,action)
        w.workspace._instruction_test_active=True;w.workspace._instruction_test_context=worker.context
        worker.progress.connect(self.on_event);worker.finished.connect(self.completed);worker.start();self.update_buttons()
    def on_event(self,kind,value):
        if kind=='status':self.status.setText(value)
        elif kind in ('assistant','error'):
            self.add_message('assistant',value if kind=='assistant' else '未完成：'+value)
            self.status.setText('本轮完成' if kind=='assistant' else '执行中断 · 可调整后重试')
        elif kind=='local_status':self.status.setText(value);self.badge.setText(value)
        elif kind=='models':
            current=self.model.currentText();self.model.clear();self.model.addItems(value);self.model.setEditText(current if current in value or not value else value[0])
            self.status.setText('连接成功 · '+str(len(value))+' 个模型');self.badge.setText('模型已连接')
        elif kind=='drafts':self.render_drafts(value)
        elif kind=='tool_start':
            frame=QFrame();frame.setObjectName('agentTool');layout=QVBoxLayout(frame);layout.setContentsMargins(10,6,10,6)
            button=QToolButton();button.setText('◌ '+value['name']+' · 执行中');button.setCheckable(True);button.setToolButtonStyle(Qt.ToolButtonTextOnly)
            detail=QPlainTextEdit(json.dumps(value,ensure_ascii=False,indent=2));detail.setReadOnly(True);detail.setMaximumHeight(160);detail.hide();button.toggled.connect(detail.setVisible)
            layout.addWidget(button);layout.addWidget(detail);self.message_layout.insertWidget(self.message_layout.count()-1,frame);self._cards.append(frame);self._tool_card=(button,detail);self._trim_cards();self.scroll_bottom()
        elif kind=='tool_result' and self._tool_card:
            button,detail=self._tool_card;button.setText(('✓ ' if value['ok'] else '! ')+value['tool']+(' · 完成' if value['ok'] else ' · 未完成'))
            detail.appendPlainText(json.dumps(value,ensure_ascii=False,indent=2));self._tool_card=None
    def completed(self):
        worker=self.worker;worker.wait();self.worker=None
        if getattr(self.window.workspace,'_instruction_test_context',None) is worker.context:
            self.window.workspace._instruction_test_active=False;self.window.workspace._instruction_test_context=None
        worker.deleteLater();self.render_drafts();self.update_buttons()
        if self._tool_card:
            self._tool_card[0].setText('已中断 · 请重新查看结果');self._tool_card=None
    def stop(self):
        if self.worker:self.worker.context.stop_requested=True;self.status.setText('正在停止…');self.stop_button.setEnabled(False)
    def render_drafts(self,snapshot=None):
        drafts=self.session.drafts if snapshot is None else [InstructionDraft.from_mapping(d) for d in snapshot]
        self.preview.setRowCount(len(drafts));self.drafts_button.setText(f'草稿 {len(drafts)}')
        for row,draft in enumerate(drafts):
            self.preview.setItem(row,0,QTableWidgetItem(draft.type_id));self.preview.setItem(row,1,QTableWidgetItem(json.dumps(draft.parameters,ensure_ascii=False)))
        if drafts:self.details.setCurrentIndex(0);self.details.show()
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
        if self.window.command_thread.isRunning() or getattr(self.window.workspace,'_instruction_test_active',False):return
        try:
            validated=[]
            for i,draft in enumerate(self.session.drafts):
                editor=get_instruction_spec(draft.type_id).create_editor(parent=self,draft=draft)
                try:validated.append(editor.get_draft())
                except Exception as error:raise ValueError(f'第 {i+1} 行：{error}') from error
                finally:editor.deleteLater()
            controls=any(d.type_id in ('循环','条件循环','条件判断','报错跳转','变量比较','暂不运行以下指令','暂不运行以上指令','终止流程','运行项目') for d in validated)
            workspace=self.window.workspace;ids=workspace.repository.append_recording(validated,connect=not controls)
            self.written=True;workspace.reload_graph();workspace.graphFinalized.emit(False);self.update_buttons()
            self.status.setText(f'已写入 {len(ids)} 条指令'+(' · 包含流程控制，请在流程图连接分支' if controls else ' · 已同步表格和流程图'))
        except Exception as error:QMessageBox.warning(self,'请检查草稿',str(error))
    def export(self):
        path,_=QFileDialog.getSaveFileName(self,'导出指令草稿','anclicker-agent.json','JSON (*.json)')
        if path:
            try:
                from pathlib import Path
                Path(path).write_text(json.dumps(export_drafts(self.session.drafts),ensure_ascii=False,indent=2),encoding='utf-8')
            except OSError as error:QMessageBox.warning(self,'导出失败',str(error))
    def import_recording(self):
        page=self.window.view_workspace.web_recording_page
        if self.busy or page.busy:return
        if not page.drafts:self.status.setText('网页录制中还没有可导入的草稿');return
        if self.written:self.session.drafts=[];self.written=False
        self.session.drafts.extend(deepcopy(page.drafts));self.render_drafts();self.update_buttons();self.status.setText('已导入网页录制草稿，可继续对话修改')
    def new_chat(self):
        if self.busy:return
        if self.unsaved and QMessageBox.question(self,'新对话','清空尚未写入的指令草稿？')!=QMessageBox.Yes:return
        self.session.close();self.session=create_agent_session();self.written=False;self._tool_card=None
        for card in self._cards:self.message_layout.removeWidget(card);card.deleteLater()
        self._cards=[];self.render_drafts();self.welcome();self.update_buttons();self.status.setText('新对话 · 准备就绪')
    def start_local(self):
        self.backend.setCurrentIndex(0);self.endpoint.setText('http://127.0.0.1:8766/v1');self.model.setEditText('anclicker-small');self.mode.setCurrentIndex(0)
        self.status.setText('正在检测资源并启动模型…');self.start_worker('',action='local')
    def refresh_resources(self):
        if self.backend.currentData()!='compatible' or self.endpoint.text().rstrip('/')!='http://127.0.0.1:8766/v1':return
        from agent_local import _manager
        snapshot=_manager.snapshot();status=snapshot['status']
        if status=='模型尚未启动':return
        label=('GPU' if status.startswith('GPU') else 'CPU') if '已就绪' in status else ('已释放 · 按需唤醒' if '释放' in status or '已停止' in status else '模型加载中' if '加载' in status else status)
        self.badge.setText(label+((' · RAM '+str(snapshot['memory_mb'])+' MB') if snapshot['memory_mb'] else ''))
        self.badge.setToolTip(status+'；空闲 '+str(snapshot['idle_seconds'])+' 秒后释放')
    def stop_local(self):
        from agent_local import stop_local_model
        try:stop_local_model();self.status.setText('已释放本机模型，下次消息自动唤醒');self.refresh_resources()
        except RuntimeError as error:QMessageBox.information(self,'模型正在使用',str(error))
    def shutdown(self):
        if self.busy:raise RuntimeError('请先停止对话 Agent')
        self.session.close()
        from agent_local import stop_local_model
        try:stop_local_model(adopt=False)
        except RuntimeError:pass  # Another app window is still using the shared model.
    def apply_theme(self,mode):
        light=mode=='light'
        bg,surface,ink,dim,line,accent=('#f7f7f8','#ffffff','#202535','#7a8194','#e3e6ef','#6c5ce7') if light else ('#09090b','#1d202a','#e9ecf5','#8c94a8','#303644','#9d92ff')
        self.scroll.viewport().setStyleSheet(f'background:{bg};')
        self.messages.setObjectName('agentMessages');self.messages.setStyleSheet(f'QWidget#agentMessages {{background:{bg};}}')
        self.setStyleSheet(f'''QWidget#agentPage {{background:{bg}; color:{ink};}}
        QWidget#agentPage QPushButton {{padding:7px 12px;border-radius:9px;border:1px solid {line};background:{surface};color:{ink};}}
        QWidget#agentPage QPushButton#accentButton {{background:{accent};color:{'#ffffff' if light else '#191528'};font-weight:600;}}
        QWidget#agentPage QPushButton:disabled {{color:{dim};}}
        QLabel#agentBrand {{font-size:20px;font-weight:700;color:{ink};}}
        QLabel#agentBadge {{color:{accent};background:{surface};border:1px solid {line};border-radius:10px;padding:4px 10px;}}
        QLabel#agentHint,QLabel#agentStatus {{color:{dim};font-size:11px;}}
        QFrame#agentAssistant,QFrame#agentComposer,QFrame#agentTool {{background:{surface};border:1px solid {line};border-radius:14px;}}
        QFrame#agentUser {{background:{'#ece9ff' if light else '#30294b'};border:1px solid {line};border-radius:14px;}}
        QFrame#agentAssistant QLabel,QFrame#agentUser QLabel {{background:transparent;border:0;color:{ink};}}
        QFrame#agentComposer QPlainTextEdit {{background:transparent;border:0;color:{ink};font-size:14px;}}
        QPushButton#agentSuggestion {{text-align:left;padding:12px;border-radius:10px;background:{surface};border:1px solid {line};color:{ink};}}
        QLabel#agentSection {{font-size:18px;font-weight:600;}}
        ''')
