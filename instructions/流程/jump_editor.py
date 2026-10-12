"""Shared behavior; each jump instruction retains its own generated UI."""
from pathlib import Path
from qt_compat.QtCore import QEvent
from qt_compat.QtWidgets import QFileDialog
from instructions.common import SchemaInstructionEditor
from flow_jumps import target_config


class JumpEditor(SchemaInstructionEditor):
    PREFIXES = ('',)

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.test_button.setEnabled(False)
        self.test_button.setToolTip('跳转需完整流程上下文；保存后在主界面运行，可随时停止。')
        for prefix in self.PREFIXES:
            self._controls[prefix+'跳转方式'].currentTextChanged.connect(self._update_targets)
            control = self._controls[prefix+'项目路径']
            control.setAcceptDrops(True)
            control.setPlaceholderText('拖入 .xlsx 项目，或点击浏览；支持相对路径及变量')
            control.installEventFilter(self)
        self._update_targets()

    def _update_targets(self, *_):
        for prefix in self.PREFIXES:
            mode = self._controls[prefix+'跳转方式'].currentText()
            self._controls[prefix+'目标行'].setEnabled(mode in ('当前项目行','其他项目行'))
            self._controls[prefix+'项目路径'].setEnabled(mode == '其他项目行')
            index = next(i for i,f in enumerate(self.FIELDS) if f.key == prefix+'项目路径')
            getattr(self.ui, f'auxiliary_{index}').setEnabled(mode == '其他项目行')

    def get_draft(self):
        draft = super().get_draft()
        for prefix in self.PREFIXES:
            target_config(draft.parameters, prefix)
        return draft

    def _run_auxiliary(self, key):
        if key.endswith('项目路径'):
            path, _ = QFileDialog.getOpenFileName(self,'选择目标项目',self._controls[key].text(),'An Clicker 项目 (*.xlsx)')
            if path: self._controls[key].setText(path)
            return
        super()._run_auxiliary(key)

    def eventFilter(self, watched, event):
        if watched in [self._controls[p+'项目路径'] for p in self.PREFIXES] and event.type() in (
                QEvent.Type.DragEnter,QEvent.Type.DragMove,QEvent.Type.Drop):
            urls=event.mimeData().urls()
            if len(urls)==1 and urls[0].isLocalFile() and Path(urls[0].toLocalFile()).suffix.lower()=='.xlsx':
                if event.type()==QEvent.Type.Drop: watched.setText(urls[0].toLocalFile())
                event.acceptProposedAction()
            else: event.ignore()
            return True
        return super().eventFilter(watched,event)
