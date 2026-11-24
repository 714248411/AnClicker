import json
from anclicker.instructions.common import SchemaInstructionEditor
from anclicker.instructions.网页抓取工具.网页框选区域提取.schema import FIELDS
from anclicker.ui.instruction_editors.extensions.extraction_export import ExportUi
from anclicker.ui.instruction_editors.extensions.crawl_preview import CrawlResultDialog
from anclicker.platform.qt_compat.QtCore import QThread
from anclicker.platform.qt_compat.QtWidgets import QLabel,QSpinBox,QFormLayout,QPushButton,QHBoxLayout,QInputDialog
from anclicker.platform.rpa_bridge import get_bridge
from anclicker.domain.web_urls import normalize_web_url

class RegionUi(ExportUi):
    def setupUi(self,dialog):
        super().setupUi(dialog)
        self.hint.setText('先在 AnClicker 打开网页 → 框选区域 → 提取预览。按当前视野中的位置提取；窗口大小、缩放或滚动改变后需重新框选。Esc 取消框选。')
        self.parameterLabel_0.setText('提取范围')
        self.parameter_0.hide();self.parameter_0.setReadOnly(True)
        self.summary=QLabel('尚未框选');self.summary.setWordWrap(True)
        self.parameterFormLayout.itemAt(0,QFormLayout.FieldRole).layout().insertWidget(0,self.summary,1)
        self.browse.setText('框选网页区域')
        old=self.parameter_1;self.parameterFormLayout.removeWidget(old);old.hide();old.deleteLater()
        self.parameter_1=QSpinBox();self.parameter_1.setRange(500,200000);self.parameter_1.setValue(20000)
        self.parameterFormLayout.setWidget(1,QFormLayout.FieldRole,self.parameter_1)
        self.parameterLabel_1.setText('最大字符数')
        self.open_page=QPushButton('打开网页')
        self.preview=QPushButton('提取预览')
        self.web_actions=QHBoxLayout()
        self.web_actions.addWidget(self.open_page)
        self.web_actions.addWidget(self.preview)
        self.rootLayout.insertLayout(2,self.web_actions)
        self.status=QLabel();self.status.setWordWrap(True);self.rootLayout.insertWidget(3,self.status)

class RegionWorker(QThread):
    def __init__(self,parent,params):
        super().__init__(parent);self.params=params;self.result=None;self.error=None
    def run(self):
        bridge=get_bridge()
        if not bridge.lock.acquire(blocking=False):
            self.error='浏览器正在执行其他指令，请稍后重试';return
        try:
            if self.params['action']=='open':
                self.result=bridge.execute({'id':'openUrl','params':{'url':self.params['url'],'engine':'Chrome','target':'新窗口','loginMode':'独立登录(每次全新)','waitType':'加载完成'}},timeout=130)['result']
                return
            if bridge.process is None or bridge.process.poll() is not None:raise ValueError('请先用 AnClicker 打开网页')
            self.result=bridge.execute({'id':'acRegion','params':self.params},timeout=130)['result']
        except Exception as error:self.error=str(error)
        finally:bridge.lock.release()

class InstructionEditor(SchemaInstructionEditor):
    TYPE_ID=DISPLAY_NAME='网页框选区域提取'
    FIELDS=FIELDS
    UI_CLASS=RegionUi
    def __init__(self,parent=None,draft=None,context=None):
        self.worker=None
        super().__init__(parent,draft,context)
        self.ui.open_page.clicked.connect(self.open_webpage)
        self.ui.browse.clicked.connect(lambda:self.start_region('select'))
        self.ui.preview.clicked.connect(lambda:self.start_region('extract'))
        self.ui.parameter_0.textChanged.connect(self.update_summary)
        self.update_summary()
    def update_summary(self,*_):
        try:
            r=json.loads(self.ui.parameter_0.text())
            self.ui.summary.setText(f"位置 ({r['x']:.0f}, {r['y']:.0f}) · 大小 {r['w']:.0f} × {r['h']:.0f} · 视野 {r['width']} × {r['height']}")
        except (ValueError,KeyError,TypeError):self.ui.summary.setText('尚未框选')
    def open_webpage(self):
        if self.worker:return
        previous=getattr(self,'_last_url','')
        if not previous:
            try:previous=json.loads(self.ui.parameter_0.text()).get('url','')
            except (ValueError,TypeError,AttributeError):pass
        address,accepted=QInputDialog.getText(self,'打开网页','输入网页地址，例如 example.com',text=previous)
        if not accepted:return
        try:address=normalize_web_url(address)
        except ValueError as error:
            self.ui.status.setText(str(error));return
        self._last_url=address
        self.begin_worker({'action':'open','url':address},'正在用 AnClicker 内置浏览器打开网页…')

    def start_region(self,action):
        if self.worker:return
        try:
            params={'action':action}
            if action=='extract':params.update(region=json.loads(self.ui.parameter_0.text()),maxChars=self.ui.parameter_1.value())
        except ValueError:
            self.ui.status.setText('请先框选网页区域');return
        self.begin_worker(params,'请在网页拖动框选，Esc 取消。' if action=='select' else '正在提取当前网页区域…')

    def begin_worker(self,params,status):
        self.worker=RegionWorker(self,params)
        for w in (self.ui.open_page,self.ui.browse,self.ui.preview,self.ui.testButton,self.button_box):w.setEnabled(False)
        self.ui.status.setText(status)
        self.worker.finished.connect(self.region_finished);self.worker.start()
    def region_finished(self):
        worker,self.worker=self.worker,None
        for w in (self.ui.open_page,self.ui.browse,self.ui.preview,self.ui.testButton,self.button_box):w.setEnabled(True)
        if worker.error:self.ui.status.setText(worker.error)
        elif worker.params['action']=='open':
            self.ui.parameter_0.clear()
            self.ui.status.setText('网页已打开，请调整到需要的位置，再点击“框选网页区域”。')
        elif worker.params['action']=='select':
            self.ui.parameter_0.setText(json.dumps(worker.result,ensure_ascii=False));self.ui.status.setText('框选完成，可点击“提取预览”核对内容。');self.raise_();self.activateWindow()
        else:
            self.ui.status.setText('提取完成，可直接另存为 Word、Excel、TXT。')
            CrawlResultDialog(worker.result,self,'正文').exec()
        worker.deleteLater()
    def done(self,code):
        if self.worker:
            self.ui.status.setText('正在打开网页，请等待完成。' if self.worker.params['action']=='open' else '正在框选或提取，请在网页按 Esc 取消框选后关闭。');return
        super().done(code)
    def closeEvent(self,event):
        if self.worker:event.ignore()
        else:super().closeEvent(event)
