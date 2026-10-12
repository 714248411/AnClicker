"""Public embeddable node editor widget."""

from __future__ import annotations

from qt_compat.QtCore import Signal
from qt_compat.QtWidgets import QHBoxLayout, QLabel, QToolButton, QVBoxLayout, QWidget

from node_editor.scene import NodeScene
from node_editor.specs import normalize_specs
from node_editor.view import NodeView


class NodeEditorWidget(QWidget):
    """Host-neutral single-flow instruction canvas.

    The widget never mutates application data.  Drop, edit, copy, delete, run,
    reorder and position changes are emitted for the host to validate and
    persist.  The host refreshes the canvas with :meth:`load_graph` afterwards.
    """

    instructionDropped = Signal(str, float, float)
    instructionCreateRequested = Signal(str, float, float)
    commandActivated = Signal(object)
    copyRequested = Signal(object)
    deleteRequested = Signal(object)
    runSingleRequested = Signal(object)
    runFromRequested = Signal(object)
    reorderPreview = Signal(object)
    reorderCommitted = Signal(object)
    graphCommitted = Signal(object, object, float, float)
    positionCommitted = Signal(object, float, float)
    sizeCommitted = Signal(object, float, float)
    connectionRequested = Signal(object, object)
    branchConnectionRequested = Signal(object, object, int)
    deleteConnectionsRequested = Signal(object, str)
    noteChanged = Signal(object, str)
    saveTemplateRequested = Signal(object, str)
    insertTemplateRequested = Signal(str, float, float)
    manageTemplatesRequested = Signal()

    def __init__(self, parent_=None):
        super().__init__(parent_)
        self.scene = NodeScene(self)
        self.view = NodeView(self.scene, self)
        self.fit_button = QToolButton(self)
        self.fit_button.setText("适应视图")
        self.fit_button.setObjectName("fitGraphButton")
        self.zoom_out_button = QToolButton(self)
        self.zoom_out_button.setText("−")
        self.zoom_in_button = QToolButton(self)
        self.zoom_in_button.setText("+")
        self.template_button = QToolButton(self)
        self.template_button.setText("模板管理")
        self.count_label = QLabel("节点：0    连线：0", self)
        self.selection_label = QLabel("未选择", self)
        self.zoom_label = QLabel("缩放：100%", self)

        toolbar_layout_ = QHBoxLayout()
        toolbar_layout_.setContentsMargins(6, 4, 6, 4)
        toolbar_layout_.addWidget(self.fit_button)
        toolbar_layout_.addWidget(self.zoom_out_button)
        toolbar_layout_.addWidget(self.zoom_in_button)
        toolbar_layout_.addWidget(self.template_button)
        toolbar_layout_.addStretch(1)

        status_layout_ = QHBoxLayout()
        status_layout_.setContentsMargins(6, 3, 6, 3)
        status_layout_.addWidget(self.count_label)
        status_layout_.addWidget(self.selection_label, 1)
        status_layout_.addWidget(self.zoom_label)

        layout_ = QVBoxLayout(self)
        layout_.setContentsMargins(0, 0, 0, 0)
        layout_.setSpacing(0)
        layout_.addLayout(toolbar_layout_)
        layout_.addWidget(self.view, 1)
        layout_.addLayout(status_layout_)

        self.fit_button.clicked.connect(self.view.fit_graph)
        self.zoom_out_button.clicked.connect(self.view.zoom_out)
        self.zoom_in_button.clicked.connect(self.view.zoom_in)
        self.template_button.clicked.connect(self.manageTemplatesRequested)
        self.scene.graphChanged.connect(self._update_counts)
        self.scene.selectionChanged.connect(self._update_selection)
        self.view.zoomChanged.connect(self._update_zoom)

        self.view.instructionDropped.connect(self.instructionDropped)
        self.view.instructionCreateRequested.connect(self.instructionCreateRequested)
        self.scene.commandActivated.connect(self.commandActivated)
        self.view.copyRequested.connect(self.copyRequested)
        self.view.deleteRequested.connect(self.deleteRequested)
        self.view.runSingleRequested.connect(self.runSingleRequested)
        self.view.runFromRequested.connect(self.runFromRequested)
        self.view.deleteConnectionsRequested.connect(self.deleteConnectionsRequested)
        self.view.noteChanged.connect(self.noteChanged)
        self.view.saveTemplateRequested.connect(self.saveTemplateRequested)
        self.view.insertTemplateRequested.connect(self.insertTemplateRequested)
        self.scene.reorderPreview.connect(self.reorderPreview)
        self.scene.reorderCommitted.connect(self.reorderCommitted)
        self.scene.graphCommitted.connect(self.graphCommitted)
        self.scene.positionCommitted.connect(self.positionCommitted)
        self.scene.sizeCommitted.connect(self.sizeCommitted)
        self.scene.connectionRequested.connect(self.connectionRequested)
        self.scene.branchConnectionRequested.connect(self.branchConnectionRequested)
        self.set_theme("dark")

    def load_graph(self, nodes_, edges_, specs_, allow_incomplete=False) -> None:
        if self.view.cutter.active:
            self.view.cutter.cancel()
        normalized_specs_ = normalize_specs(specs_)
        self.view.set_instruction_types(normalized_specs_)
        self.scene.load_graph(
            nodes_, edges_, normalized_specs_, allow_incomplete=allow_incomplete
        )

    def selected_command_ids(self) -> list:
        return self.scene.selected_command_ids()

    def focus_command(self, command_id_) -> bool:
        node_ = self.scene.focus_command(command_id_)
        if node_ is None:
            return False
        self.view.centerOn(node_)
        self.view.ensureVisible(node_)
        return True

    def _update_counts(self, node_count_, edge_count_) -> None:
        self.count_label.setText(f"节点：{node_count_}    连线：{edge_count_}")

    def _update_selection(self) -> None:
        selected_count_ = len(self.selected_command_ids())
        self.selection_label.setText(
            f"已选择：{selected_count_}" if selected_count_ else "未选择"
        )

    def _update_zoom(self, percent_) -> None:
        self.zoom_label.setText(f"缩放：{percent_:.4g}%")

    def set_theme(self, mode: str) -> None:
        from node_editor.style import BACKGROUND_COLOR, apply_theme

        apply_theme(mode)
        self.scene.setBackgroundBrush(BACKGROUND_COLOR)
        self.scene.invalidate(self.scene.sceneRect())
        for item in self.scene.items():
            item.update()
        if mode == "light":
            background, text, button, border, hover, muted = (
                "#f7f7f8", "#2f2f2f", "#ffffff", "#d9d9e0", "#e6e6e9", "#6b6b75"
            )
        else:
            background, text, button, border, hover, muted = (
                "#09090b", "#f1f1f3", "#222225", "#2b2b30", "#2c2c30", "#a1a1aa"
            )
        self.setStyleSheet(
            f"""
            QWidget {{ background: {background}; color: {text}; }}
            QToolButton {{ color: {text}; background: {button};
                          border: 1px solid {border}; border-radius: 8px;
                          padding: 5px 10px; }}
            QToolButton:hover {{ background: {hover}; border-color: {'#0088ff' if mode == 'dark' else '#6574d8'}; }}
            QLabel {{ color: {muted}; padding: 0 6px; }}
            """
        )
