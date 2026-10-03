from PySide6.QtCore import QPointF, Qt
from PySide6.QtGui import QAction, QColor, QKeySequence
from PySide6.QtWidgets import (
    QDockWidget,
    QLabel,
    QMainWindow,
    QMessageBox,
    QToolBar,
    QTreeWidgetItem,
)

from node_test.scene import NodeScene
from node_test.style import NODE_TYPES
from node_test.view import NodePalette, NodeView


class NodeEditorWindow(QMainWindow):
    def __init__(self):
        super().__init__()
        self.setWindowTitle("Clicker 节点编辑器 UI 原型")
        self.resize(1280, 780)
        self.setMinimumSize(900, 560)

        self.scene = NodeScene(self)
        self.view = NodeView(self.scene, self)
        self.setCentralWidget(self.view)

        self.palette = NodePalette(self)
        self._build_palette()
        self._build_dock()
        self._build_toolbar()
        self._build_status_bar()
        self._apply_style()

        self.palette.nodeActivated.connect(self.add_node_to_center)
        self.scene.graphChanged.connect(self.update_counts)
        self.view.zoomChanged.connect(self.update_zoom)
        self.scene.selectionChanged.connect(self.update_selection)
        self.update_counts(0, 0)
        self.update_zoom(100)

        self._add_demo_nodes()

    def _build_palette(self):
        categories = {}
        for category in ("流程", "动作", "等待", "判断"):
            category_item = QTreeWidgetItem([category])
            category_item.setFlags(category_item.flags() & ~Qt.ItemFlag.ItemIsDragEnabled)
            self.palette.addTopLevelItem(category_item)
            categories[category] = category_item

        for node_type, definition in NODE_TYPES.items():
            item = QTreeWidgetItem([node_type])
            item.setData(0, Qt.ItemDataRole.UserRole, node_type)
            item.setForeground(0, definition["color"].lighter(150))
            categories[definition["category"]].addChild(item)
        self.palette.expandAll()

    def _build_dock(self):
        dock = QDockWidget("节点", self)
        dock.setObjectName("nodePaletteDock")
        dock.setAllowedAreas(Qt.DockWidgetArea.LeftDockWidgetArea | Qt.DockWidgetArea.RightDockWidgetArea)
        dock.setFeatures(QDockWidget.DockWidgetFeature.DockWidgetMovable)
        dock.setMinimumWidth(210)
        dock.setWidget(self.palette)
        self.addDockWidget(Qt.DockWidgetArea.LeftDockWidgetArea, dock)

    def _build_toolbar(self):
        toolbar = QToolBar("画布工具", self)
        toolbar.setObjectName("canvasToolbar")
        toolbar.setMovable(False)
        self.addToolBar(toolbar)

        add_action = QAction("添加节点", self)
        add_action.setToolTip("在画布中心添加一个图像点击节点")
        add_action.triggered.connect(lambda: self.add_node_to_center("图像点击"))
        toolbar.addAction(add_action)

        delete_action = QAction("删除选中", self)
        delete_action.setShortcut(QKeySequence.StandardKey.Delete)
        delete_action.triggered.connect(self.scene.delete_selected)
        self.addAction(delete_action)
        toolbar.addAction(delete_action)

        toolbar.addSeparator()
        fit_action = QAction("适应视图", self)
        fit_action.setShortcut(QKeySequence("F"))
        fit_action.triggered.connect(self.view.fit_graph)
        self.addAction(fit_action)
        toolbar.addAction(fit_action)

        clear_action = QAction("清空画布", self)
        clear_action.triggered.connect(self.confirm_clear)
        toolbar.addAction(clear_action)

    def _build_status_bar(self):
        self.count_label = QLabel()
        self.selection_label = QLabel("未选择")
        self.zoom_label = QLabel()
        self.statusBar().addWidget(self.count_label)
        self.statusBar().addWidget(self.selection_label, 1)
        self.statusBar().addPermanentWidget(self.zoom_label)

    def _apply_style(self):
        self.setStyleSheet(
            """
            QMainWindow { background: #171a21; }
            QToolBar { background: #222732; border: 0; spacing: 6px; padding: 6px; }
            QToolButton { color: #dfe6ee; background: #303744; border: 1px solid #414b5d;
                          border-radius: 4px; padding: 6px 11px; }
            QToolButton:hover { background: #3a4352; border-color: #58a6ff; }
            QDockWidget { color: #e6edf3; font-weight: 600; }
            QDockWidget::title { background: #222732; padding: 8px; }
            QTreeWidget { background: #1d222b; color: #dfe6ee; border: 0; padding: 5px; }
            QTreeWidget::item { min-height: 28px; border-radius: 4px; }
            QTreeWidget::item:hover { background: #2c3340; }
            QTreeWidget::item:selected { background: #1f6feb; color: white; }
            QStatusBar { background: #222732; color: #9aa7b5; }
            QStatusBar QLabel { color: #9aa7b5; padding: 0 8px; }
            """
        )

    def _add_demo_nodes(self):
        start = self.scene.add_node("开始", QPointF(-44.0, -240.0))
        action = self.scene.add_node("图像点击", QPointF(-44.0, -110.0))
        condition = self.scene.add_node("变量判断", QPointF(-44.0, 20.0))
        end = self.scene.add_node("结束", QPointF(-44.0, 150.0))
        self.scene.connect_ports(start.output_ports[0], action.input_ports[0])
        self.scene.connect_ports(action.output_ports[0], condition.input_ports[0])
        self.scene.connect_ports(condition.output_ports[0], end.input_ports[0])
        self.scene.clearSelection()

    def add_node_to_center(self, node_type):
        position = self.view.mapToScene(self.view.viewport().rect().center())
        self.scene.add_node(node_type, position)

    def confirm_clear(self):
        if not self.scene.items():
            return
        result = QMessageBox.question(
            self,
            "清空画布",
            "确定删除画布中的全部节点和连线吗？",
            QMessageBox.StandardButton.Yes | QMessageBox.StandardButton.No,
            QMessageBox.StandardButton.No,
        )
        if result == QMessageBox.StandardButton.Yes:
            self.scene.clear_graph()

    def update_counts(self, node_count, edge_count):
        self.count_label.setText("节点：{}    连线：{}".format(node_count, edge_count))

    def update_zoom(self, percent):
        self.zoom_label.setText("缩放：{}%".format(percent))

    def update_selection(self):
        count = len(self.scene.selectedItems())
        self.selection_label.setText("已选择：{}".format(count) if count else "未选择")
