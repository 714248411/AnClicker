"""Convenient native editor for Crawl4AI instructions."""
from anclicker.instructions.common import SchemaInstructionEditor, actions
from anclicker.instructions.网页抓取工具.Crawl4AI网页抓取.schema import FIELDS
from anclicker.instructions.网页抓取工具.Crawl4AI网页抓取.executor import InstructionExecutor
from anclicker.ui.generated.instructions.网页抓取工具.Crawl4AI网页抓取.Crawl4AI网页抓取_ui import Ui_InstructionEditor
from anclicker.ui.instruction_editors.extensions.crawl_preview import CrawlPreviewWorker, CrawlResultDialog
from anclicker.platform.qt_compat.QtCore import Qt
from anclicker.platform.qt_compat.QtWidgets import (QApplication, QPushButton, QHBoxLayout,
    QLabel, QComboBox, QInputDialog, QMessageBox, QDialog)
from anclicker.platform.rpa_bridge import get_bridge
from anclicker.domain.instructions import ExecutionContext
from anclicker.domain.web_urls import normalize_web_url


class InstructionEditor(SchemaInstructionEditor):
    TYPE_ID = 'Crawl4AI网页抓取'
    DISPLAY_NAME = 'Crawl4AI 网页抓取'
    FIELDS = FIELDS
    UI_CLASS = Ui_InstructionEditor

    def __init__(self, parent=None, draft=None, context=None):
        self._worker = None
        self._pending_done = None
        self._last_result = None
        super().__init__(parent, draft, context)
        self._controls['网址'].setPlaceholderText('例如 hao123.com，或使用 {{网址变量}}')
        self._controls['选择器'].setPlaceholderText('例如 article 或 #content；留空抓取整页')
        self._controls['等待元素'].setPlaceholderText('例如 .article-loaded；等待动态内容出现')
        self._controls['网址'].editingFinished.connect(self._normalize_address)
        self.ui.testButton.setText('测试并保存变量')
        self.ui.testButton.setToolTip('使用现有指令测试流程执行，并写入指定变量')
        tip = QLabel('填写网址 → 抓取预览 → 确认参数加入流程。预览不写入变量。独立抓取不继承已登录网页的账号状态。')
        tip.setWordWrap(True)
        self.ui.rootLayout.insertWidget(1, tip)
        row = QHBoxLayout()
        self.paste_button = QPushButton('粘贴网址')
        self.browser_button = QPushButton('选择已打开网页')
        self.paste_button.clicked.connect(self._paste_address)
        self.browser_button.clicked.connect(self._choose_browser)
        row.addWidget(self.paste_button)
        row.addWidget(self.browser_button)
        row.addStretch()
        self.ui.rootLayout.insertLayout(2, row)
        presets = QHBoxLayout()
        presets.addWidget(QLabel('快速方案'))
        self.preset = QComboBox()
        self.preset.addItems(['保持当前设置', '整页内容', '文章区域', '整理网页链接'])
        self.preset.activated[int].connect(self._apply_preset)
        presets.addWidget(self.preset, 1)
        self.advanced_button = QPushButton('高级设置')
        self.advanced_button.setCheckable(True)
        self.advanced_button.toggled.connect(self._show_advanced)
        presets.addWidget(self.advanced_button)
        self.ui.rootLayout.insertLayout(3, presets)
        advanced = any(self._control_value(self._controls[f.key]) != f.default for f in FIELDS[2:6])
        self.advanced_button.setChecked(advanced)
        self._show_advanced(advanced)
        preview_row = QHBoxLayout()
        self.preview_button = QPushButton('抓取预览')
        self.stop_preview_button = QPushButton('停止抓取')
        self.last_result_button = QPushButton('查看上次结果')
        self.stop_preview_button.setEnabled(False)
        self.last_result_button.setEnabled(False)
        self.preview_button.clicked.connect(self._start_preview)
        self.stop_preview_button.clicked.connect(self._stop_preview)
        self.last_result_button.clicked.connect(self._show_result)
        for button in (self.preview_button, self.stop_preview_button, self.last_result_button):
            preview_row.addWidget(button)
        self.ui.rootLayout.insertLayout(5, preview_row)
        self.preview_status = QLabel('等待抓取；完成后可预览、复制和导出所需内容。')
        self.preview_status.setWordWrap(True)
        self.preview_status.setTextFormat(Qt.PlainText)
        self.ui.rootLayout.insertWidget(6, self.preview_status)
        for button in (self.paste_button, self.browser_button, self.advanced_button, self.preview_button, self.stop_preview_button, self.last_result_button):
            button.setMinimumHeight(32)
        self.resize(800, min(660, self.screen().availableGeometry().height() - 60))

    def _show_advanced(self, enabled):
        for index in range(2, 6):
            self.ui.parameterFormLayout.setRowVisible(index, enabled)
        self.advanced_button.setText('收起高级设置' if enabled else '高级设置')

    def _apply_preset(self, index):
        if not index:
            return
        self._controls['选择器'].setText('article, main, [role="main"]' if index == 2 else '')
        self._controls['格式'].setCurrentText('链接' if index == 3 else 'Markdown')
        self._controls['等待元素'].clear()
        if index == 2:
            self.advanced_button.setChecked(True)
            self.preview_status.setText('文章区域适用于有 article/main 标签的网站；预览为空时可改用整页内容。')

    def _normalize_address(self):
        text = self._controls['网址'].text().strip()
        if not text or any(mark in text for mark in ('{{', '☾', '$' + '{')):
            return
        try:
            self._controls['网址'].setText(normalize_web_url(text))
        except ValueError:
            pass  # Validation and preview present errors when the user is ready.

    def _paste_address(self):
        self._controls['网址'].setText(QApplication.clipboard().text().strip())
        self._normalize_address()

    def _choose_browser(self):
        bridges = [get_bridge()]
        owner = self.parentWidget()
        while owner is not None:
            workspace = getattr(owner, 'view_workspace', None)
            agent = getattr(workspace, 'agent_page', None)
            if agent is not None and not agent.busy:
                bridge = getattr(agent.session, 'bridge', None)
                if bridge is not None and bridge not in bridges:
                    bridges.append(bridge)
            owner = owner.parentWidget()
        self._begin_worker(CrawlPreviewWorker(self, bridges=bridges), '正在读取 AnClicker 已打开的网页…')

    def _start_preview(self):
        if self._worker is not None:
            return
        try:
            draft = self.get_draft()
            context = self.context or ExecutionContext()
            p = draft.parameters
            resolve = lambda key: actions.substitute_variables(context, str(p.get(key, '')))
            request = dict(url=normalize_web_url(resolve('网址')), selector=resolve('选择器'),
                           wait_for=resolve('等待元素'), timeout=int(p['超时']), max_chars=int(p['最大字符数']))
        except (ValueError, TypeError) as error:
            QMessageBox.warning(self, '请检查抓取设置', str(error))
            return
        self._begin_worker(CrawlPreviewWorker(self, request=request), '正在抓取网页，可随时停止…')

    def _begin_worker(self, worker, text):
        if self._worker is not None:
            worker.deleteLater()
            return
        self._worker = worker
        self.preview_status.setText(text)
        self._set_busy(True)
        worker.finished.connect(self._preview_finished)
        worker.start()

    def _set_busy(self, busy):
        for widget in (self.ui.parameterGroupBox, self.ui.commonGroupBox, self.ui.testButton,
                       self.paste_button, self.browser_button, self.preset, self.preview_button,
                       self.advanced_button, self.runtime_advanced_button):
            widget.setEnabled(not busy)
        self.button_box.button(self.button_box.StandardButton.Ok).setEnabled(not busy)
        self.stop_preview_button.setEnabled(busy)
        self.last_result_button.setEnabled(not busy and self._last_result is not None)

    def _stop_preview(self):
        if self._worker is not None:
            self._worker.context.stop_requested = True
            self.preview_status.setText('正在停止并释放抓取资源…')
            self.stop_preview_button.setEnabled(False)

    def _preview_finished(self):
        worker, self._worker = self._worker, None
        worker.deleteLater()
        self._set_busy(False)
        if self._pending_done is not None:
            super().done(self._pending_done)
            return
        if worker.context.stop_requested:
            self.preview_status.setText('已停止抓取。')
        elif worker.error:
            self.preview_status.setText('未完成：' + worker.error)
        elif worker.request is None:
            tabs = worker.result or []
            if not tabs:
                self.preview_status.setText('没有可读取的网页。请先用 AnClicker 打开网页，或直接粘贴网址；正在执行任务的浏览器会跳过。')
                return
            choices = [f"{i+1}. {tab.get('title') or '网页'} — {tab['url']}" for i, tab in enumerate(tabs)]
            if len(tabs) == 1:
                index = 0
            else:
                choice, accepted = QInputDialog.getItem(self, '选择网页', 'AnClicker 已打开的网页', choices, 0, False)
                if not accepted:
                    self.preview_status.setText('已取消选择网页。')
                    return
                index = choices.index(choice)
            self._controls['网址'].setText(tabs[index]['url'])
            self.preview_status.setText('已填入网页地址，点击“抓取预览”查看结果。')
        else:
            self._last_result = worker.result
            self.last_result_button.setEnabled(True)
            self.preview_status.setText('抓取完成，可查看、复制或保存结果；预览没有写入变量。')
            self._show_result()

    def _show_result(self):
        if self._last_result is not None:
            CrawlResultDialog(self._last_result, self, self._controls['格式'].currentText()).exec()

    def done(self, code):
        if self._worker is not None:
            self._pending_done = code
            self._stop_preview()
            return
        super().done(code)

    def reject(self):
        self.done(QDialog.Rejected)

    def closeEvent(self, event):
        if self._worker is not None:
            self.reject()
            event.ignore()
            return
        super().closeEvent(event)
