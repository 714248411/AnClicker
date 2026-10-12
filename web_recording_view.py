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
        title=QLabel('网页录制');title.setObjectName('pageTitle');layout.addWidget(title)
        tip=QLabel('在极速网页AC中录制点击、文本输入、回车与Tab，自动保留操作间隔和停止前的等待。\n停止后预览，再写入表格与流程图。当前录制网页主文档；密码输入不记录。')
        tip.setWordWrap(True);layout.addWidget(tip)
        address=QHBoxLayout();address.addWidget(QLabel('网页地址'))
        self.url=QLineEdit();self.url.setPlaceholderText('https://example.com');address.addWidget(self.url,1);layout.addLayout(address)
        controls=QHBoxLayout()
        self.start_button=QPushButton('打开网页并开始录制');self.start_button.setObjectName('accentButton')
        self.stop_button=QPushButton('停止网页录制');self.stop_button.setObjectName('dangerButton')
        self.write_button=QPushButton('写入表格与流程图');self.clear_button=QPushButton('清空预览')
        for button in (self.start_button,self.stop_button,self.write_button,self.clear_button):controls.addWidget(button)
        controls.addStretch();layout.addLayout(controls)
        self.connect_option=QCheckBox('自动连接录制流程');self.connect_option.setChecked(True);layout.addWidget(self.connect_option)
        self.status=QLabel('未录制 · 操作间隔会生成等待指令');self.status.setWordWrap(True);layout.addWidget(self.status)
        self.preview=QTableWidget(0,3);self.preview.setHorizontalHeaderLabels(['序号','指令','参数'])
        self.preview.setEditTriggers(QAbstractItemView.EditTrigger.NoEditTriggers)
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
        self.write_button.setEnabled(not self.busy and bool(self.drafts) and not self.written)
        self.clear_button.setEnabled(not self.busy and bool(self.drafts))
        self.connect_option.setEnabled(not self.busy)
    def begin(self):
        if self.busy:return
        if self.window.command_thread.isRunning() or self.window.view_workspace.recording_page.busy or getattr(self.window.workspace,'_instruction_test_active',False) or getattr(self.window,'_update_preparing',False):
            QMessageBox.warning(self,'无法录制','请先停止任务、键鼠录制或指令测试。');return
        from web_urls import normalize_web_url
        try:
            url=normalize_web_url(self.url.text())
        except ValueError as error:
            QMessageBox.warning(self,'网页地址无效',str(error));return
        if self.drafts and not self.written and QMessageBox.question(self,'重新录制','丢弃尚未写入的网页录制并重新开始？')!=QMessageBox.StandardButton.Yes:return
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
        self.drafts=events_to_web_drafts(self.recorded_url,self.events,self.elapsed)
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
