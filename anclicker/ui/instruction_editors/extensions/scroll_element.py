"""Element scrolling settings, ordered like the user's workflow."""
from anclicker.ui.instruction_editors.rpa_instruction import RpaInstructionEditor
from anclicker.platform.qt_compat.QtWidgets import QPushButton,QInputDialog,QMessageBox
from anclicker.domain.instructions import CommandRecord,ExecutionContext
from anclicker.ui.instruction_editors.test_runner import run_cancellable_test
from anclicker.instructions.registry import get_instruction_spec

class ScrollElementEditor(RpaInstructionEditor):
    def __init__(self,*args,**kwargs):
        super().__init__(*args,**kwargs)
        self.open_web_button=QPushButton('打开网页',self)
        self.open_web_button.clicked.connect(self.open_web)
        self.web_window.layout().insertWidget(1,self.open_web_button)
        self.test_button.setText('测试滚动')
        self._controls['selector'].setPlaceholderText('点击“拾取元素”，或填写文字、CSS、XPath')
        self.locator_status.setText('只滚动，不点击。靠近页面首尾时停在可滚动边界；未加载的内容需先加载。')
        self._controls['by'].currentTextChanged.connect(self.update_locator_rows)
        self.update_locator_rows()

    def update_locator_rows(self,*_):
        enabled=self._controls['by'].currentText()=='锚点定位'
        for index,field in enumerate(self.FIELDS):
            if field.key in ('anchor','anchorRel'):
                getattr(self.ui,'label_'+str(index)).setVisible(enabled)
                getattr(self.ui,'container_'+str(index),self._controls[field.key]).setVisible(enabled)

    def load_draft(self,draft):
        super().load_draft(draft)
        self.update_locator_rows()

    def _validate_parameters(self,params):
        super()._validate_parameters(params)
        if not str(params.get('selector','')).strip():raise ValueError('请先拾取或填写目标元素')
        if params.get('by')=='锚点定位' and not str(params.get('anchor','')).strip():raise ValueError('请设置辅助锚点')

    def open_web(self):
        url,ok=QInputDialog.getText(self,'打开网页','网页地址',text='https://')
        if not ok:return
        try:
            context=ExecutionContext()
            run_cancellable_test(get_instruction_spec('打开网页'),CommandRecord(None,'打开网页',{'url':url.strip(),'target':'新窗口','waitType':'加载完成'}),context,self)
            if not context.stop_requested:
                self.web_window.set_selection(None)
                self.web_window.refresh()
        except Exception as error:QMessageBox.warning(self,'打开网页失败',str(error))
