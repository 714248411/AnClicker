"""Linked Clicker workspaces and the light/dark desktop themes."""
from __future__ import annotations
from anclicker.ui.workspace_constants import CODE_SETTING, CODE_GRAPH_SIGNATURE_SETTING
from anclicker.app.state import application_state
import weakref
import hashlib
import json
from anclicker.platform.qt_compat.QtCore import QSignalBlocker, Qt
from anclicker.platform.qt_compat.QtWidgets import QDialog, QHBoxLayout, QLabel, QListWidget, QListWidgetItem, QMessageBox, QPushButton, QSplitter, QVBoxLayout, QWidget
from anclicker.instructions.registry import iter_instruction_specs

from anclicker._imports import DeferredImports as _DeferredImports

# Dependencies declared here retain their existing on-demand loading boundaries.
_module_imports = _DeferredImports(globals(), {
    'GuidedCodeEditor': ('from', 'anclicker.ui.guided_code_editor', ('GuidedCodeEditor',), 0),
    'prepare_instruction_conversion': ('from', 'anclicker.domain.instruction_code', ('prepare_instruction_conversion',), 0),
    'InstructionConversionDialog': ('from', 'anclicker.ui.instruction_conversion_dialog', ('InstructionConversionDialog',), 0),
})


class CodeWorkspace:

    def __init__(self, workspace):
        self.workspace = weakref.proxy(workspace)

    def _build_code_view(self) -> QWidget:
        workspace = self.workspace
        page = QWidget()
        page.setObjectName('multifunctionView')
        layout = QVBoxLayout(page)
        header = QHBoxLayout()
        title = QLabel('多功能代码')
        title.setObjectName('pageTitle')
        workspace.code_status = QLabel('修改会自动保存在当前任务中')
        workspace.code_status.setObjectName('mutedText')
        regenerate = QPushButton('按当前流程重新生成')
        regenerate.clicked.connect(workspace.regenerate_code)
        header.addWidget(title)
        header.addWidget(workspace.code_status)
        header.addStretch(1)
        header.addWidget(regenerate)
        workspace.write_code_button = QPushButton('写入表格与流程图')
        workspace.write_code_button.setToolTip('按代码更新当前流程；遗漏参数填入默认值，写入后可在表格中修改。')
        workspace.write_code_button.clicked.connect(workspace.write_code_to_flow)
        header.addWidget(workspace.write_code_button)
        layout.addLayout(header)
        splitter = QSplitter(Qt.Orientation.Horizontal)
        workspace.command_list = QListWidget()
        workspace.command_list.setMinimumWidth(190)
        workspace.command_list.setMaximumWidth(290)
        for spec in iter_instruction_specs():
            item = QListWidgetItem(f'{spec.category}  /  {spec.display_name}')
            item.setData(Qt.ItemDataRole.UserRole, spec.type_id)
            workspace.command_list.addItem(item)
        workspace.command_list.itemDoubleClicked.connect(workspace._insert_command_hint)
        GuidedCodeEditor = _module_imports.load('GuidedCodeEditor')
        workspace.code_editor = GuidedCodeEditor()
        palette = workspace.window.workspace.palette
        workspace.code_editor.set_guidance_enabled(palette.guidance_enabled)
        palette.guidanceEnabledChanged.connect(workspace.code_editor.set_guidance_enabled)
        hint = QLabel('中文输入提示：↑↓选择，Tab / 回车插入，Esc关闭；Ctrl+空格查看下一步。模板参数可继续修改。')
        hint.setWordWrap(True)
        hint.setVisible(palette.guidance_enabled)
        palette.guidanceEnabledChanged.connect(hint.setVisible)
        layout.addWidget(hint)
        workspace.code_editor.textChanged.connect(workspace._schedule_code_save)
        splitter.addWidget(workspace.command_list)
        splitter.addWidget(workspace.code_editor)
        splitter.setStretchFactor(1, 1)
        layout.addWidget(splitter, 1)
        return page

    def _load_code(self) -> None:
        workspace = self.workspace
        if workspace._code_dirty:
            return
        (snapshot, validation_error) = workspace._current_graph_state()
        signature = workspace._graph_signature(snapshot)
        saved_signature = str(workspace.window.db.get_setting_value(CODE_GRAPH_SIGNATURE_SETTING) or '')
        text = str(workspace.window.db.get_setting_value(CODE_SETTING) or '')
        if not text or saved_signature != signature:
            text = workspace._generated_code(snapshot, validation_error)
            workspace.window.db.set_setting_value(CODE_SETTING, text)
            workspace.window.db.set_setting_value(CODE_GRAPH_SIGNATURE_SETTING, signature)
        workspace._loading_code = True
        if workspace.code_editor.toPlainText() != text:
            with QSignalBlocker(workspace.code_editor):
                workspace.code_editor.setPlainText(text)
        workspace._loading_code = False
        workspace.code_status.setText('修改会自动保存在当前任务中' if validation_error is None else '已同步流程草稿，可按连线优先、其余按添加顺序运行')

    def write_code_to_flow(self) -> None:
        workspace = self.workspace
        window = workspace.window
        if not application_state(window).can_edit_project():
            window.statusBar.showMessage('请先停止任务、录制或指令测试。', 4000)
            return
        try:
            prepare_instruction_conversion = _module_imports.load('prepare_instruction_conversion')
            InstructionConversionDialog = _module_imports.load('InstructionConversionDialog')
            plan = prepare_instruction_conversion(workspace.code_editor.toPlainText())
            dialog = InstructionConversionDialog(plan, window)
            if dialog.exec() != QDialog.DialogCode.Accepted:
                return
            ids = window.workspace.repository.write_instruction_code(plan.entries)
        except Exception as error:
            QMessageBox.warning(window, '写入失败，原流程未改变', str(error))
            return
        workspace._code_dirty = False
        window.workspace.clear_connection_history()
        window.workspace.reload_graph()
        window.workspace.graphFinalized.emit(False)
        workspace._sync_code_if_needed(force=True)
        workspace.refresh_all()
        workspace.code_status.setText(f'已写入 {len(ids)} 条指令；可在表格中修改参数')
        window.statusBar.showMessage('表格与流程图已同步；缺省参数已补齐，可双击表格修改。', 5000)

    def regenerate_code(self) -> None:
        workspace = self.workspace
        workspace._sync_code_if_needed(force=True)
        workspace.refresh_summary()
        workspace.window.statusBar.showMessage('已根据当前流程重新生成多功能代码。', 3000)

    def _current_graph_state(self):
        workspace = self.workspace
        try:
            snapshot = workspace.window.workspace.repository.validate_graph()
            return (snapshot, None)
        except Exception as error:
            try:
                snapshot = workspace.window.workspace.repository.execution_snapshot()
                return (snapshot, '可执行：连线优先，其余按添加顺序运行')
            except Exception as execution_error:
                return (workspace.window.workspace.repository.snapshot(), f'无法执行：{execution_error}')

    @staticmethod
    def _graph_signature(snapshot) -> str:
        payload = {'commands': [{'id': command.id, 'type': command.type_id, 'parameters': command.parameters, 'repeat': command.repeat_count, 'error': command.error_policy, 'note': command.note, 'order': command.order} for command in snapshot.commands], 'edges': [{'source': edge.source, 'target': edge.target, 'kind': edge.kind} for edge in snapshot.edges]}
        encoded = json.dumps(payload, ensure_ascii=False, sort_keys=True, separators=(',', ':')).encode('utf-8')
        return hashlib.sha256(encoded).hexdigest()

    def _sync_code_if_needed(self, *, force: bool=False) -> bool:
        workspace = self.workspace
        (snapshot, validation_error) = workspace._current_graph_state()
        signature = workspace._graph_signature(snapshot)
        saved_signature = str(workspace.window.db.get_setting_value(CODE_GRAPH_SIGNATURE_SETTING) or '')
        saved_code = str(workspace.window.db.get_setting_value(CODE_SETTING) or '')
        if not force and saved_signature == signature and saved_code:
            return False
        text = workspace._generated_code(snapshot, validation_error)
        workspace._loading_code = True
        with QSignalBlocker(workspace.code_editor):
            workspace.code_editor.setPlainText(text)
        workspace._loading_code = False
        workspace._code_dirty = False
        workspace.window.db.set_setting_value(CODE_SETTING, text)
        workspace.window.db.set_setting_value(CODE_GRAPH_SIGNATURE_SETTING, signature)
        workspace.code_status.setText('流程、表格与多功能已同步' if validation_error is None else '已同步流程草稿，可按连线优先、其余按添加顺序运行')
        return True

    def _generated_code(self, snapshot=None, validation_error=None) -> str:
        workspace = self.workspace
        if snapshot is None:
            (snapshot, validation_error) = workspace._current_graph_state()
        commands = list(snapshot.commands)
        lines = ['# Clicker 多功能代码（由流程图同步）', '# 状态：流程完整，可执行' if validation_error is None else f'# 状态：流程草稿，{validation_error}', f'# 流程签名：{workspace._graph_signature(snapshot)[:16]}', '# 在流程不变时可继续编辑；流程改变后会按最新内容重新同步。', '']
        nodes_by_command = {node.command_id: node for node in snapshot.nodes if node.command_id is not None}
        for (sequence, command) in enumerate(commands, start=1):
            params = json.dumps(command.parameters, ensure_ascii=False, sort_keys=True)
            note = f'  # {command.note}' if command.note else ''
            node = nodes_by_command.get(command.id)
            display_name = node.display_name if node is not None else command.type_id
            lines.append(f'# [{sequence}] #{command.id} {display_name}')
            lines.append(f'{command.type_id}({params}, 重复次数={command.repeat_count}, 异常处理={command.error_policy!r}){note}')
        if snapshot.edges:
            nodes = {node.node_id: node for node in snapshot.nodes}
            kind_names = {0: '下一步', 1: '是', 2: '否', 3: '循环体', 4: '完成', 5: '报错', 6: '异常跳转', 7: '比较是跳转', 8: '比较否跳转'}
            lines.extend(['', '# 流程连线（由流程图自动同步）'])
            for edge in snapshot.edges:
                source = nodes[edge.source]
                target = nodes[edge.target]
                source_name = '开始' if source.command_id is None else f'#{source.command_id} {source.display_name}'
                target_name = '结束' if target.command_id is None else f'#{target.command_id} {target.display_name}'
                lines.append(f"# {source_name} --{kind_names.get(edge.kind, '下一步')}--> {target_name}")
        if not commands:
            lines.append('# 当前流程还没有指令，请先到流程图或表格视图添加。')
        return '\n'.join(lines) + '\n'

    def _insert_command_hint(self, item: QListWidgetItem) -> None:
        workspace = self.workspace
        type_id = item.data(Qt.ItemDataRole.UserRole)
        workspace.code_editor.insert_command(type_id)
        workspace.code_editor.setFocus()

    def _schedule_code_save(self) -> None:
        workspace = self.workspace
        if workspace._loading_code:
            return
        workspace._code_dirty = True
        workspace.code_status.setText('正在保存……')
        workspace._code_save_timer.start()

    def _save_code(self) -> None:
        workspace = self.workspace
        workspace._code_save_timer.stop()
        if not workspace._code_dirty:
            return
        workspace.window.db.set_setting_value(CODE_SETTING, workspace.code_editor.toPlainText())
        workspace._code_dirty = False
        workspace.code_status.setText('已自动保存')
