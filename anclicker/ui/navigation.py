"""Linked Clicker workspaces and the light/dark desktop themes."""
from __future__ import annotations
from anclicker.ui.workspace_constants import MAIN_VIEW, TABLE_VIEW, FLOW_VIEW, CODE_VIEW, RECORDING_VIEW, WEB_RECORDING_VIEW, AGENT_VIEW
import weakref
import json
from anclicker.ui.compact_position import DEFAULT_COMPACT_SIZE, LAST_SIZE_SETTING, SIZE_MODE_SETTING
from anclicker.platform.qt_compat.QtCore import QObject, QEvent, QSize, Qt, QTimer
from anclicker.platform.qt_compat.QtGui import QAction, QKeySequence
from anclicker.platform.qt_compat.QtWidgets import QMenu

from anclicker._imports import DeferredImports as _DeferredImports

# Dependencies declared here retain their existing on-demand loading boundaries.
_module_imports = _DeferredImports(globals(), {
    'install_title_bar': ('from', 'anclicker.ui.window_chrome', ('install_title_bar',), 0),
    'CompactWorkspace': ('from', 'anclicker.ui.compact_workspace', ('CompactWorkspace',), 0),
    'LayoutPresets': ('from', 'anclicker.ui.layout_presets', ('LayoutPresets',), 0),
    'install_view_shortcuts': ('from', 'anclicker.ui.view_shortcuts', ('install_view_shortcuts',), 0),
    'install_menu_styling': ('from', 'anclicker.ui.context_menu_style', ('install_menu_styling',), 0),
    'open_advanced_timing': ('from', 'anclicker.ui.timing_dialog', ('open_advanced_timing',), 0),
    'ToolbarCustomization': ('from', 'anclicker.ui.toolbar_customization', ('ToolbarCustomization',), 0),
})


def create_controls_menu_action(workspace):
    action = QAction('显示控制栏', workspace.window)
    action.setCheckable(True)
    action.setChecked(not workspace.controls_collapsed)
    action.toggled.connect(workspace.controls_action.setChecked)
    workspace.controls_action.toggled.connect(action.setChecked)
    workspace.controls_menu_action = action
    return action


def restore_default_window_size(workspace):
    """Restore the current window mode's size without rearranging any panels."""
    window=workspace.window
    compact=getattr(getattr(workspace,'compact',None),'active',False)
    width,height=(340,460) if compact else (1180,720)
    window.showNormal()
    screen=window.screen()
    if screen is not None:
        area=screen.availableGeometry()
        width=min(width,area.width());height=min(height,area.height())
    window.resize(width,height)
    if hasattr(workspace, 'docking'): workspace.docking.reset_parameter_sizes()
    if screen is not None:
        frame=window.frameGeometry()
        x=max(area.left(),min(frame.left(),area.right()-frame.width()+1))
        y=max(area.top(),min(frame.top(),area.bottom()-frame.height()+1))
        window.move(x,y)
    window.statusBar.showMessage('已恢复默认界面大小',3000)


def restore_default_compact_size(workspace):
    """Use the default compact size once, then continue remembering resizes."""
    window=workspace.window
    window.db.set_setting_value(SIZE_MODE_SETTING,'last')
    window.db.set_setting_value(LAST_SIZE_SETTING,json.dumps(dict(zip(('width','height'),DEFAULT_COMPACT_SIZE))))
    compact=getattr(workspace,'compact',None)
    if compact is not None and compact.active:
        restore_default_window_size(workspace)
        compact._save_position()
    window.statusBar.showMessage('已恢复默认小窗大小；下次调整后继续记忆上次大小。',4000)


class _ToolbarDockOnDoubleClick(QObject):
    """Return a floating toolbar to its last dock area from empty-space double clicks."""

    def __init__(self, window, toolbar):
        super().__init__(toolbar)
        self.window = window
        self.toolbar = toolbar
        area = window.toolBarArea(toolbar)
        self.area = area if area != Qt.ToolBarArea.NoToolBarArea else Qt.ToolBarArea.TopToolBarArea
        toolbar.installEventFilter(self)
        toolbar.topLevelChanged.connect(self._remember_area)

    def _remember_area(self, floating=False):
        if not floating and not self.toolbar.isFloating():
            area = self.window.toolBarArea(self.toolbar)
            if area != Qt.ToolBarArea.NoToolBarArea:
                self.area = area

    def eventFilter(self, watched, event):
        if watched is self.toolbar:
            if event.type() in (QEvent.Type.Move, QEvent.Type.Show):
                self._remember_area()
            elif (event.type() == QEvent.Type.MouseButtonDblClick
                  and event.button() == Qt.MouseButton.LeftButton
                  and self.toolbar.isFloating()):
                point = event.position().toPoint()
                action = self.toolbar.actionAt(point)
                # Buttons, embedded controls and the overflow button retain their own behavior.
                if action is not None and not action.isSeparator():
                    return False
                if self.toolbar.childAt(point) is not None:
                    return False
                event.accept()
                QTimer.singleShot(0, self._dock)
                return True
        return super().eventFilter(watched, event)

    def _dock(self):
        if not self.toolbar.isFloating():
            return
        area = self.area
        if not (self.toolbar.allowedAreas() & area):
            area = next((candidate for candidate in (
                Qt.ToolBarArea.TopToolBarArea, Qt.ToolBarArea.BottomToolBarArea,
                Qt.ToolBarArea.LeftToolBarArea, Qt.ToolBarArea.RightToolBarArea)
                if self.toolbar.allowedAreas() & candidate), None)
        if area is None:
            return
        self.window.removeToolBar(self.toolbar)
        self.toolbar.setParent(self.window, Qt.WindowType.Widget)
        self.window.addToolBar(area, self.toolbar)
        self.toolbar.show()


class NavigationController:

    def __init__(self, workspace):
        self.workspace = weakref.proxy(workspace)

    def _build_navigation(self) -> None:
        workspace = self.workspace
        workspace._toolbar_dock_filter = _ToolbarDockOnDoubleClick(workspace.window, workspace.window.toolBar)
        workspace.window.toolBar.setWindowTitle('显示工具栏')
        workspace.window.toolBar.toggleViewAction().setText('显示工具栏')
        workspace.window.toolBar.setIconSize(QSize(16, 16))
        toolbar_font = workspace.window.toolBar.font()
        base_size = toolbar_font.pointSize()
        toolbar_font.setPointSize(max(8, base_size - 2 if base_size > 0 else 9))
        workspace.window.toolBar.setFont(toolbar_font)
        workspace.primary_action = QAction('打开流程图', workspace.window)
        workspace.primary_action.triggered.connect(workspace.toggle_primary)
        workspace.code_action = QAction('多功能', workspace.window)
        workspace.code_action.triggered.connect(workspace.show_code)
        workspace.palette_side_action = QAction('指令栏移到右侧', workspace.window)
        workspace.palette_side_action.triggered.connect(workspace.toggle_palette_side)
        workspace.palette_collapse_action = QAction('收起指令栏', workspace.window)
        workspace.palette_collapse_action.triggered.connect(workspace.toggle_palette)
        workspace.theme_action = QAction('切换浅色', workspace.window)
        workspace.theme_action.triggered.connect(workspace.toggle_theme)
        workspace.controls_action = QAction('展开控制栏' if workspace.controls_collapsed else '收起控制栏', workspace.window)
        workspace.controls_action.setCheckable(True)
        workspace.controls_action.setChecked(not workspace.controls_collapsed)
        workspace.controls_action.toggled.connect(workspace.set_controls_visible)
        workspace.donation_action = QAction('捐赠', workspace.window)
        workspace.donation_action.triggered.connect(workspace.show_donation)
        workspace.window.toolBar.addSeparator()
        workspace.window.toolBar.addAction(workspace.primary_action)
        workspace.window.toolBar.addSeparator()
        workspace.window.toolBar.addAction(workspace.palette_collapse_action)
        workspace.window.toolBar.addAction(workspace.controls_action)
        workspace.window.menubar.addAction(workspace.donation_action)
        install_title_bar = _module_imports.load('install_title_bar')
        workspace.title_bar = install_title_bar(workspace.window, workspace.theme_action)
        workspace.title_bar.apply_theme(workspace.theme_mode, workspace.THEMES[workspace.theme_mode])
        CompactWorkspace = _module_imports.load('CompactWorkspace')
        workspace.compact = CompactWorkspace(workspace)
        menu = QMenu('视图', workspace.window)
        workspace.view_menu = menu
        view_actions = {}
        for (label, shortcut, callback) in (('主界面', 'Ctrl+1', workspace.show_main), ('表格图', 'Ctrl+2', workspace.show_table), ('流程图', 'Ctrl+3', workspace.show_flow), ('多功能', 'Ctrl+4', workspace.show_code), ('录制', 'Ctrl+6', workspace.show_recording), ('网页录制', 'Ctrl+7', workspace.show_web_recording), ('对话Ai编程', 'Ctrl+8', workspace.show_agent), ('设置变量', 'Ctrl+Shift+V', workspace.show_variables)):
            action = QAction(label, workspace.window)
            action.setShortcut(QKeySequence(shortcut))
            view_actions[label] = action
            action.triggered.connect(callback)
            menu.addAction(action)
        workspace.window.menubar.insertMenu(workspace.window.menu_4.menuAction(), menu)
        workspace.font_size_menu = QMenu('界面字号', workspace.window)
        workspace.window.menubar.insertMenu(workspace.window.menu_4.menuAction(), workspace.font_size_menu)
        for (label, amount) in [('字号+', 1), ('字号-', -1), ('字号恢复默认', None)]:
            action = workspace.font_size_menu.addAction(label)
            action.triggered.connect(lambda checked=False, step=amount: workspace.interface_scale.change(step))
        menu.addSeparator()
        workspace.window.menu_3.removeAction(workspace.window.actiong)
        workspace.window.actiong.setText('显示工具栏')
        menu.addAction(workspace.window.actiong)
        menu.addAction(create_controls_menu_action(workspace))
        workspace.restore_view_action = QAction('恢复默认界面布局', workspace.window)
        workspace.restore_view_action.triggered.connect(lambda : workspace.layout_presets.reset())
        workspace.restore_size_action = QAction('恢复默认界面大小',workspace.window)
        workspace.restore_size_action.setObjectName('actionRestoreDefaultWindowSize')
        workspace.restore_size_action.setToolTip('恢复窗口、设置面板的默认尺寸及字号，保留面板布局')
        workspace.restore_size_action.triggered.connect(lambda: restore_default_window_size(workspace))
        workspace.restore_compact_size_action=QAction('恢复默认小窗大小',workspace.window)
        workspace.restore_compact_size_action.setObjectName('actionRestoreDefaultCompactSize')
        workspace.restore_compact_size_action.setToolTip('恢复一次默认小窗尺寸并作为新的上次大小，继续选择上次大小；摆放位置保持不变')
        workspace.restore_compact_size_action.triggered.connect(lambda:restore_default_compact_size(workspace))
        workspace.layout_menu = QMenu('界面方案', workspace.window)
        workspace.window.menubar.insertMenu(menu.menuAction(), workspace.layout_menu)
        LayoutPresets = _module_imports.load('LayoutPresets')
        workspace.layout_presets = LayoutPresets(workspace, workspace.layout_menu)
        workspace.editable_view_action = menu.addAction('可编辑视图')
        workspace.editable_view_action.setCheckable(True)
        workspace.editable_view_action.setChecked(workspace.window.db.get_setting_value('可编辑视图') == 'True')
        workspace.editable_view_action.setToolTip('勾选后可拖拽或双击调整布局；默认锁定，仍可通过右键菜单选择停靠位置')
        workspace.editable_view_action.toggled.connect(lambda enabled: workspace.docking.set_editable(enabled))
        menu.addSeparator()
        workspace.flow_tips_action = menu.addAction('显示流程图操作提示')
        workspace.flow_tips_action.setCheckable(True)
        workspace.flow_tips_action.setChecked(workspace.flow_tips.expanded)
        workspace.flow_tips_action.toggled.connect(workspace.flow_tips.set_expanded)
        workspace.flow_tips.expandedChanged.connect(workspace.flow_tips_action.setChecked)
        flow_view = workspace.window.workspace.editor.view
        workspace.flow_arrows_action = menu.addAction('流程图箭头动画')
        workspace.flow_arrows_action.setCheckable(True)
        workspace.flow_arrows_action.setToolTip('勾选显示连线箭头；取消后隐藏箭头，保留连线和文字。')
        workspace.flow_arrows_action.triggered.connect(flow_view.set_arrows_visible)
        workspace.flow_continuous_action = menu.addAction('流程图持续动画')
        workspace.flow_continuous_action.setCheckable(True)
        workspace.flow_continuous_action.setToolTip('勾选持续播放；取消后仅在开始运行时播放 5 秒。')
        workspace.flow_continuous_action.triggered.connect(flow_view.set_continuous_animation)

        def sync_flow_actions(*_):
            workspace.flow_arrows_action.setChecked(flow_view.arrows_visible)
            workspace.flow_continuous_action.setChecked(flow_view.continuous_animation)
        flow_view.arrowsVisibilityChanged.connect(sync_flow_actions)
        flow_view.continuousAnimationChanged.connect(sync_flow_actions)
        menu.aboutToShow.connect(sync_flow_actions)
        sync_flow_actions()
        view_actions['指令栏收起/展开'] = workspace.palette_collapse_action
        view_actions['控制与操作收起/展开'] = workspace.controls_action
        workspace.both_panels_action = QAction('指令与控制栏同时收起/展开', workspace.window)
        def toggle_both_panels():
            show = workspace.palette_collapsed and workspace.controls_collapsed
            if workspace.palette_collapsed == show:
                workspace.toggle_palette()
            workspace.controls_action.setChecked(show)
        workspace.both_panels_action.triggered.connect(toggle_both_panels)
        view_actions['指令与控制栏同时收起/展开'] = workspace.both_panels_action
        workspace.window.addAction(workspace.both_panels_action)
        workspace.window.addAction(workspace.palette_collapse_action)
        workspace.window.addAction(workspace.controls_action)
        view_actions['显示工具栏'] = workspace.window.actiong
        guidance_action = QAction('中文编程提示', workspace.window)
        guidance_action.setCheckable(True)
        palette = workspace.window.workspace.palette
        guidance_action.setChecked(palette.guidance_enabled)
        guidance_action.toggled.connect(palette.set_guidance_enabled)
        palette.guidanceEnabledChanged.connect(guidance_action.setChecked)
        workspace.window.menu_4.addAction(guidance_action)
        view_actions['中文编程提示'] = guidance_action
        menu.addSeparator()
        install_view_shortcuts = _module_imports.load('install_view_shortcuts')
        workspace.window._view_shortcut_actions = view_actions
        workspace.window.menubar.removeAction(workspace.window.menu_3.menuAction())
        install_menu_styling = _module_imports.load('install_menu_styling')
        install_menu_styling(workspace.window)
        open_advanced_timing = _module_imports.load('open_advanced_timing')
        tools_menu = next((action.menu() for action in workspace.window.menubar.actions() if action.text().replace('&', '') == '设置'), None)
        if tools_menu is not None:
            timing_action = QAction('高级设置', tools_menu)
            entries = tools_menu.actions()
            index = entries.index(workspace.window.actions_2) + 1
            tools_menu.insertAction(entries[index] if index < len(entries) else None, timing_action)
            timing_action.setObjectName('advancedExecutionTiming')
            timing_action.triggered.connect(lambda : open_advanced_timing(workspace.window, workspace.window.db))
        ToolbarCustomization = _module_imports.load('ToolbarCustomization')
        workspace.toolbar_customization = ToolbarCustomization(workspace.window)

    def toggle_primary(self) -> None:
        workspace = self.workspace
        {FLOW_VIEW: workspace.show_table, TABLE_VIEW: workspace.show_code}.get(workspace.tabs.currentIndex(), workspace.show_flow)()

    def _show_workspace(self, index):
        workspace = self.workspace
        workspace.tabs.setCurrentIndex(index)
        if hasattr(workspace, 'docking'):
            workspace.docking.sync_visibility()

    def show_main(self):
        workspace = self.workspace
        workspace._show_workspace(MAIN_VIEW)

    def show_table(self):
        workspace = self.workspace
        workspace._show_workspace(TABLE_VIEW)

    def show_flow(self):
        workspace = self.workspace
        workspace._show_workspace(FLOW_VIEW)

    def show_code(self):
        workspace = self.workspace
        workspace._load_code()
        workspace._show_workspace(CODE_VIEW)

    def show_navigation(self):
        workspace = self.workspace
        workspace.show_main()

    def show_recording(self):
        workspace = self.workspace
        workspace._show_workspace(RECORDING_VIEW)

    def show_web_recording(self):
        workspace = self.workspace
        workspace._show_workspace(WEB_RECORDING_VIEW)

    def show_agent(self):
        workspace = self.workspace
        workspace._show_workspace(AGENT_VIEW)

    def show_beginner(self):
        workspace = self.workspace
        workspace.show_navigation()

    def show_editor(self):
        workspace = self.workspace
        workspace.show_flow()
