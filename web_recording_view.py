from responsive_layout import FlowLayout
"""Opt-in browser recording with asynchronous engine calls and a preview."""
import json
from qt_compat.QtCore import QThread, QTimer
from qt_compat.QtWidgets import (QWidget,QVBoxLayout,QHBoxLayout,QLabel,QPushButton,QLineEdit,
    QCheckBox,QTableWidget,QTableWidgetItem,QHeaderView,QAbstractItemView,QMessageBox)
from instructions.common.rpa_bridge import RpaBridge
from web_recording import events_to_web_drafts

class _BrowserWorker(QThread):
    def __init__(self, bridge, action, url, parent):
        super().__init__(parent)
        self.bridge,self.action,self.url=bridge,action,url
        self.result=None;self.error=None
    def run(self):
        try:
            if self.action=='start':
                self.bridge.execute({'id':'openUrl','params':{'url':self.url,'engine':'Chrome','target':'新窗口','loginMode':'独立登录(每次全新)','waitType':'加载完成'}})
            self.result=self.bridge.execute({'id':{'start':'acRecordStart','stop':'acRecordStop','status':'acRecordStatus'}[self.action]})['result']
        except Exception as error:
            self.error=str(error)
        finally:
            if self.action=='stop' or self.error:
                self.bridge.close()

class WebRecordingView(QWidget):
    def __init__(self, window):
        super().__init__(window)
        self.window=window;self.drafts=[];self.written=False;self.active=False;self.worker=None
        self.pending_stop=False;self.events=[];self.elapsed=0;self.recorded_url=''
        self.bridge=RpaBridge('web-recording')
        layout=QVBoxLayout(self)
        description = "操作顺序\n填写网页地址 → 打开网页并开始录制 → 在极速网页AC中操作 → 返回录制页停止 → 检查预览 → 写入表格与流程图。\n\n开始与停止\n填写完整网址（例如 https://www.example.com），点击“打开网页并开始录制”。等待状态显示“录制中”后再操作；结束时回到此页点击“停止网页录制”。网页录制使用独立登录环境，原有浏览器的登录状态不会自动带入。\n任务运行、键鼠录制、指令测试或准备更新时，请先结束相关操作，再开始网页录制。\n\n记录内容与等待\n记录网页主文档中的点击、文本输入、回车和 Tab，以及页面跳转。对同一输入框连续输入的内容可能合并成一条输入指令。\n操作间隔和最后一次操作至停止之间的等待会生成等待指令；点击或回车引起跳转时，会生成等待页面加载完成的指令。预览开头保留录制时填写的入口地址。\n当前不覆盖所有网页交互：嵌入页面（iframe）、画布、复杂拖拽等操作需检查结果，并按需补充指令。密码框输入不记录；其他输入内容可能保存在指令参数中。\n\n预览、删除与接续\n停止后可选中一行或多行，右键删除并确认。参数在写入后通过表格或流程图修改。\n接续录制：选中一条尚未写入的步骤，点击“接续录制”，新操作插入该步骤下方，原有后续步骤保留。\n接续会重新打开录制地址，不会自动执行已有步骤或恢复之前的网页状态。请留意登录和页面准备过程也可能被录入，停止后检查并删除不需要的步骤。\n\n写入与整理\n点击“写入表格与流程图”追加指令；“自动连接录制流程”用于连接本次写入的步骤。写入只是保存指令，不会立即执行。\n同一份预览只能写入一次。写入后请在表格或流程图中继续修改；清空预览不影响已写入的指令。重新录制前会确认是否丢弃未写入内容。\n\n回放前检查\n检查入口地址、元素定位、输入内容及等待时间。网页布局、登录状态或网络速度变化时，可能需要重新拾取元素，或补充“等待元素出现”“等待页面加载完成”等指令。\n最多记录 10000 个事件。页面异常或录制中断后，请先检查已保留的预览，再决定写入或重新录制。"
        from recording_help import recording_header
        layout.addLayout(recording_header(self, '网页录制', description))
        address=QHBoxLayout();address.addWidget(QLabel('网页地址'))
        self.url=QLineEdit();self.url.setPlaceholderText('https://example.com');address.addWidget(self.url,1);layout.addLayout(address)
        controls=FlowLayout()
        self.start_button=QPushButton('打开网页并开始录制');self.start_button.setObjectName('accentButton')
        self.stop_button=QPushButton('停止网页录制');self.stop_button.setObjectName('dangerButton')
        self.continue_button=QPushButton('接续录制')
        self.continue_button.setToolTip('选中步骤后，在该步骤下方插入新录制内容')
        from recording_continuation import begin_continuation
        self.continue_button.clicked.connect(lambda: begin_continuation(self))
        self.write_button=QPushButton('写入表格与流程图');self.clear_button=QPushButton('清空预览')
        for button in (self.start_button,self.stop_button,self.continue_button,self.write_button,self.clear_button):controls.addWidget(button)
        controls.addStretch();layout.addLayout(controls)
        self.connect_option=QCheckBox('自动连接录制流程');self.connect_option.setChecked(True);layout.addWidget(self.connect_option)
        self.status=QLabel('未录制 · 操作间隔会生成等待指令');self.status.setWordWrap(True);layout.addWidget(self.status)
        self.preview=QTableWidget(0,3);self.preview.setHorizontalHeaderLabels(['序号','指令','参数'])
        self.preview.setEditTriggers(QAbstractItemView.EditTrigger.NoEditTriggers)
        from recording_preview_menu import RecordingPreviewMenu
        self.preview_menu = RecordingPreviewMenu(self)
        self.preview.horizontalHeader().setSectionResizeMode(2,QHeaderView.ResizeMode.Stretch);layout.addWidget(self.preview,1)
        self.timer=QTimer(self);self.timer.setInterval(500);self.timer.timeout.connect(self.poll)
        self.start_button.clicked.connect(self.begin);self.stop_button.clicked.connect(self.finish)
        self.write_button.clicked.connect(self.write);self.clear_button.clicked.connect(self.clear)
        self.update_buttons()
    @property
    def busy(self):return self.active or self.worker is not None
    @property
    def unsaved(self):return self.busy or bool(self.drafts and not self.written)
    def update_buttons(self):
        self.start_button.setEnabled(not self.busy);self.url.setEnabled(not self.busy)
        self.stop_button.setEnabled(self.busy and not self.pending_stop)
        self.continue_button.setEnabled(not self.busy and bool(self.drafts) and not self.written)
        self.write_button.setEnabled(not self.busy and bool(self.drafts) and not self.written)
        self.clear_button.setEnabled(not self.busy and bool(self.drafts))
        self.connect_option.setEnabled(not self.busy)
    def begin(self, *, continuation=False):
        if self.busy:return
        if self.window.command_thread.isRunning() or self.window.view_workspace.recording_page.busy or getattr(self.window.workspace,'_instruction_test_active',False) or getattr(self.window,'_update_preparing',False):
            QMessageBox.warning(self,'无法录制','请先停止任务、键鼠录制或指令测试。');return
        from web_urls import normalize_web_url
        try:
            url=normalize_web_url(self.url.text())
        except ValueError as error:
            QMessageBox.warning(self,'网页地址无效',str(error));return
        if not continuation and self.drafts and not self.written and QMessageBox.question(self,'重新录制','丢弃尚未写入的网页录制并重新开始？')!=QMessageBox.StandardButton.Yes:return
        self.drafts=[];self.written=False;self.events=[];self.elapsed=0;self.pending_stop=False
        self.recorded_url=url;self.preview.setRowCount(0)
        self.status.setText('正在打开网页，完成后开始计时…');self._request('start')
    def _request(self, action):
        if self.worker is not None:return
        self.worker=_BrowserWorker(self.bridge,action,self.recorded_url,self)
        self.worker.finished.connect(self._completed);self.worker.start();self.update_buttons()
    def poll(self):
        if self.active and self.worker is None:self._request('status')
    def finish(self):
        if not self.busy:return
        self.pending_stop=True;self.timer.stop();self.status.setText('正在停止并整理网页录制…')
        if self.worker is None:self._request('stop')
        self.update_buttons()
    def _completed(self):
        worker=self.worker;worker.wait();self.worker=None
        action,result,error=worker.action,worker.result,worker.error;worker.deleteLater()
        if error:
            self.active=False;self.pending_stop=False;self.timer.stop()
            if self.events:self._render()
            elif getattr(self, "_continuation", None) is not None:
                from recording_continuation import finish_continuation
                finish_continuation(self, [])
                self.render_preview()
            self.status.setText('网页录制已停止：'+error);self.update_buttons();return
        if action=='start':
            # Keep the requested entry URL, not a site's redirect/intermediate page.
            self.active=True
            self.timer.start();self.status.setText('录制中 · 请在极速网页AC操作，回到此页停止')
        else:
            self.events=result.get('events',self.events);self.elapsed=result.get('elapsed',self.elapsed)
            if action=='stop' or not result.get('active'):
                self.active=False;self.timer.stop();self._render();self.pending_stop=False
                self.status.setText(f'录制结束 · {len(self.drafts)} 条指令（含等待，尚未写入）'+(' · 已达10000事件上限' if result.get('full') else ''))
            else:self.status.setText(f'录制中 · {result["count"]} 个事件 · {self.elapsed/1000:.1f} 秒')
        if self.pending_stop and self.active:self._request('stop')
        self.update_buttons()
    def _render(self):
        from recording_continuation import finish_continuation
        finish_continuation(self, events_to_web_drafts(self.recorded_url,self.events,self.elapsed), web=True)
        self.render_preview()
    def render_preview(self):
        self.preview.setRowCount(len(self.drafts))
        for row,draft in enumerate(self.drafts):
            for col,text in enumerate((str(row+1),draft.type_id,json.dumps(draft.parameters,ensure_ascii=False))):
                self.preview.setItem(row,col,QTableWidgetItem(text))
    def write(self):
        if self.busy or self.written or not self.drafts:return
        if self.window.command_thread.isRunning() or self.window.view_workspace.recording_page.busy:return
        try:
            workspace=self.window.workspace
            ids=workspace.repository.append_recording(self.drafts,connect=self.connect_option.isChecked())
            self.written=True;self.update_buttons();workspace.reload_graph();workspace.graphFinalized.emit(False)
            self.status.setText(f'已追加 {len(ids)} 条网页录制指令 · 表格与流程图已同步')
        except Exception as error:QMessageBox.warning(self,'写入失败',str(error))
    def clear(self):
        if self.busy:return
        if self.drafts and not self.written and QMessageBox.question(self,'清空预览','丢弃未写入的网页录制？')!=QMessageBox.StandardButton.Yes:return
        self.drafts=[];self.events=[];self.written=False;self.preview.setRowCount(0);self.status.setText('网页录制预览已清空');self.update_buttons()
    def shutdown(self):
        self.timer.stop()
        if self.worker is not None:raise RuntimeError('请先停止网页录制')
        self.active=False;self.bridge.close()
