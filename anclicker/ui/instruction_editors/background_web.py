"""CDP settings; refresh targets asynchronously without blocking drag/drop."""
import re
import threading
from anclicker.platform.qt_compat.QtCore import QObject, Signal, QTimer
from anclicker.platform.qt_compat.QtWidgets import QLabel, QPushButton, QMessageBox, QInputDialog
from anclicker.ui.instruction_editors.editor import SchemaInstructionEditor
from anclicker.ui.instruction_editors.vision_tools import VisionUi
from anclicker.ui.web_window_selector import WebWindowSelector
from anclicker.domain.instructions import CommandRecord, ExecutionContext
from anclicker.instructions.registry import get_instruction_spec
from anclicker.platform.rpa_bridge import get_bridge
from anclicker.platform.cdp_discovery import discover_endpoints
from anclicker.ui.instruction_editors.test_runner import run_cancellable_test

class BackgroundWebUi(VisionUi):
    def setupUi(self, dialog):
        super().setupUi(dialog)
        self.errorPolicyComboBox.clear()
        self.errorPolicyComboBox.addItems(['提示异常并暂停','自动跳过','提示异常并停止'])

class WindowResult(QObject):
    ready = Signal(object, str)

class BackgroundWebEditor(SchemaInstructionEditor):
    UI_CLASS = BackgroundWebUi
    def __init__(self, *args, **kwargs):
        self._saved_web_window = None
        self._refreshing = False
        self._closed = False
        super().__init__(*args, **kwargs)
        self.status = QLabel('正在刷新 CDP 窗口…', self)
        self.status.setWordWrap(True)
        self.web_window = WebWindowSelector(lambda: None, self._saved_web_window, self)
        self.refresh_button = self.web_window.findChildren(QPushButton)[0]
        self.refresh_button.clicked.disconnect()
        self.refresh_button.clicked.connect(self.refresh_windows)
        self.refresh_button.setText('刷新窗口')
        self.open_button = QPushButton('打开网页', self)
        self.open_button.clicked.connect(self.open_web)
        self.web_window.layout().insertWidget(1, self.open_button)
        self.web_window.combo.setToolTip('列出 AnClicker 网页和已启用 CDP 的外部浏览器页面。普通 Chrome / Edge 未启用远程调试时无法直接连接。后台执行不激活窗口，取点时会显示网页。')
        self.ui.visionForm.insertRow(0, 'CDP 窗口', self.web_window)
        self.ui.rootLayout.insertWidget(1, self.status)
        if 'points' in self._controls:
            self._controls['points'].setPlaceholderText('100,200' if self.COMMAND_ID == 'backgroundClick' else '100,200; 300,400')
            button = QPushButton('网页取点', self)
            button.clicked.connect(self.pick_points)
            self.ui.tools.addWidget(button)
        self._result = WindowResult(self)
        self._result.ready.connect(self._windows_ready)
        self._initial_refresh = QTimer(self)
        self._initial_refresh.setSingleShot(True)
        self._initial_refresh.timeout.connect(self.refresh_windows)
        self._initial_refresh.start(0)
        self.finished.connect(self._finish)
        if 'customKey' in self._controls:
            self._controls['key'].currentTextChanged.connect(self._update_key)
            self._update_key()

    def _update_key(self, *_):
        for widget in self.ui.rows['customKey']:
            widget.setVisible(self._controls['key'].currentText() == '自定义')

    def _finish(self, *_):
        self._closed = True
        self._initial_refresh.stop()

    def refresh_windows(self):
        self._request('acListCdpWindows', {})

    def _request(self, command, params):
        if self._refreshing or self._closed: return
        self._refreshing = True
        self._opening = params if command in ('acOpenCdpPage','acOpenRemotePage') else None
        self.refresh_button.setEnabled(False)
        self.open_button.setEnabled(False)
        self.status.setText('正在打开网页…' if command in ('acOpenCdpPage','acOpenRemotePage') else '正在刷新 CDP 窗口…')
        signal = self._result
        def work():
            try:
                request_params = dict(params, cdpEndpoints=discover_endpoints())
                response = get_bridge().execute({'id':command,'params':request_params}, timeout=45)
                pages = response.get('result')
                if not isinstance(pages,list): raise RuntimeError('未收到网页窗口列表')
                error = ''
            except Exception as exc:
                pages, error = [], str(exc)
            try: signal.ready.emit(pages,error)
            except RuntimeError: pass
        threading.Thread(target=work,daemon=True).start()

    def _windows_ready(self, pages, error):
        self._refreshing = False
        if self._closed: return
        self.refresh_button.setEnabled(True)
        self.open_button.setEnabled(True)
        if not error:
            self.web_window.list_windows = lambda: pages
            self.web_window.refresh()
            if self._opening and pages:
                key = self._opening.get('window', {}).get('cdpKey')
                native_pages = [p for p in pages if p.get('engine') == '内置' and p.get('cdpKey')]
                previous = self._opening.get('window', {})
                chosen = next((p for p in pages if (key and p.get('cdpKey') == key) or (previous.get('remote') and p.get('remote') and p.get('endpoint') == previous.get('endpoint') and p.get('id') == previous.get('id'))), (native_pages or pages)[-1])
                self.web_window.set_selection(chosen)
            elif self.web_window.selection() is None and len(pages)==1:
                self.web_window.set_selection(pages[0])
        self.status.setText(('操作失败：'+error) if error else ('已刷新 '+str(len(pages))+' 个窗口；通过“打开网页”创建的会话会自动保存与恢复。' if pages else '暂无可连接网页。外部 Chrome / Edge 需开启远程调试，也可点击“打开网页”创建。'))

    def open_web(self):
        selected = self.web_window.selection() or {}
        label = '网址（在所选外部浏览器标签页打开）' if selected.get('remote') else '网址（会保存到网页记录，下次恢复）'
        url, ok = QInputDialog.getText(self,'打开 CDP 网页',label,text=selected.get('url','https://'))
        if ok and url.strip():
            self._request('acOpenRemotePage' if selected.get('remote') else 'acOpenCdpPage',{'url':url.strip(),'window':selected})

    def load_draft(self, draft):
        super().load_draft(draft)
        params = draft.parameters if hasattr(draft,'parameters') else draft.get('parameters',{})
        self._saved_web_window = params.get('browserWindow')
        if hasattr(self,'web_window'): self.web_window.set_selection(self._saved_web_window)

    def get_draft(self):
        draft = super().get_draft()
        draft.parameters['browserWindow'] = self.web_window.selection()
        return draft

    def _validate_parameters(self, params):
        super()._validate_parameters(params)
        if 'points' in params:
            text = str(params['points']).strip().replace('；',';').replace('，',',')
            if not text: raise ValueError('请先设置网页点击坐标')
            if not any(mark in text for mark in ('$'+'{','{{','☾')):
                points = [part.strip() for part in text.split(';') if part.strip()]
                if not points or any(not re.fullmatch(r'\d+(?:\.\d+)?\s*,\s*\d+(?:\.\d+)?',point) for point in points):
                    raise ValueError('坐标格式为 100,200；多个点用分号分隔')
                if len(points)>1000 or (self.COMMAND_ID=='backgroundClick' and len(points)!=1):
                    raise ValueError('单点指令只能设置一个坐标；多点最多 1000 个')
            params['points'] = text
        if params.get('key')=='自定义' and not str(params.get('customKey','')).strip():
            raise ValueError('请填写自定义按键')

    def pick_points(self):
        try:
            context = ExecutionContext(variables=dict(getattr(self.context,'variables',{})))
            spec = get_instruction_spec(self.TYPE_ID)
            params = {'pickOnly':True,'points':self._controls['points'].text(),'browserWindow':self.web_window.selection()}
            run_cancellable_test(spec,CommandRecord(None,self.TYPE_ID,params),context,self)
            result = context.variables.get('网页取点结果')
            if not context.stop_requested and isinstance(result,dict) and not result.get('canceled'):
                self._controls['points'].setText('; '.join(str(p['x'])+','+str(p['y']) for p in result.get('points',[])))
        except Exception as error: QMessageBox.warning(self,'取点未完成',str(error))
