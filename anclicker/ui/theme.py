"""Workspace palette and stylesheet application."""
import os
from anclicker.platform.qt_compat.QtCore import Qt, QTimer
from anclicker.platform.qt_compat.QtGui import QColor, QPalette, QGuiApplication
from anclicker.app.paths import RESOURCE_FOLDER

THEMES = {
    "dark": {
        "bg": "#09090b", "nav": "#080809", "surface": "#18181b",
        "surface2": "#222225", "surface3": "#2c2c30", "line": "#2b2b30",
        "text": "#f1f1f3", "dim": "#a1a1aa", "accent": "#0088ff",
        "accent2": "#0965b5", "accent_text": "#ffffff", "danger": "#dc3545",
    },
    "light": {
        "bg": "#f7f7f8", "nav": "#ececf1", "surface": "#ffffff",
        "surface2": "#f1f1f3", "surface3": "#e6e6e9", "line": "#d9d9e0",
        "text": "#2f2f2f", "dim": "#6b6b75", "accent": "#5b6fdc",
        "accent2": "#495bbd", "accent_text": "#ffffff", "danger": "#d94b4b",
    },
}

def apply_theme(self) -> None:
    c = self.THEMES[self.theme_mode]
    if hasattr(self, 'agent_page'):
        self.agent_page.apply_theme(self.theme_mode)
    tabs_palette = self.tabs.palette()
    tabs_palette.setColor(QPalette.ColorRole.Window, QColor(c["bg"]))
    self.tabs.setPalette(tabs_palette)
    self.tabs.setAutoFillBackground(True)
    if hasattr(self.tabs.tabBar(), "set_theme"):
        self.tabs.tabBar().set_theme(c)
    down_arrow = os.path.join(RESOURCE_FOLDER, 'resources', 'icons', 'chevron-down.svg').replace('\\', '/')
    up_arrow = os.path.join(RESOURCE_FOLDER, 'resources', 'icons', 'chevron-up.svg').replace('\\', '/')
    try:
        scheme = (
            Qt.ColorScheme.Dark
            if self.theme_mode == "dark"
            else Qt.ColorScheme.Light
        )
        QGuiApplication.styleHints().setColorScheme(scheme)
    except AttributeError:
        pass
    if hasattr(self, "command_table"):
        table_palette = self.command_table.palette()
        for role, color in (
            (QPalette.ColorRole.Window, c["surface"]),
            (QPalette.ColorRole.Base, c["surface"]),
            (QPalette.ColorRole.AlternateBase, c["surface2"]),
            (QPalette.ColorRole.Text, c["text"]),
            (QPalette.ColorRole.WindowText, c["text"]),
            (QPalette.ColorRole.Button, c["surface2"]),
            (QPalette.ColorRole.Highlight, c["accent2"]),
            (QPalette.ColorRole.HighlightedText, c["accent_text"]),
        ):
            table_palette.setColor(role, QColor(color))
        self.command_table.setPalette(table_palette)
        self.command_table.viewport().setPalette(table_palette)
        self.command_table.viewport().setAutoFillBackground(True)
    self.window.workspace.editor.set_theme(self.theme_mode)
    controls_palette = self.window.groupBox_3.palette()
    controls_palette.setColor(QPalette.ColorRole.WindowText, QColor(c['text']))
    self.window.groupBox_3.setPalette(controls_palette)
    if hasattr(self, "title_bar"):
        self.title_bar.apply_theme(self.theme_mode, c)
    self.window.setStyleSheet(f"""
        QDockWidget {{ color: {c['text']}; font-size: 12px; border: none; }}
        QLabel#dockPanelTitle {{ background: {c['surface2']}; color: {c['text']}; font-size: 12px; border: none; border-radius: 5px; }}
        QDockWidget::title {{ background: {c['surface2']}; padding: 5px; border-radius: 5px; }}
        QMainWindow::separator {{ background: {c['bg']}; width: 5px; height: 5px; }}
        QMainWindow, QWidget#centralwidget {{ background: {c['bg']}; color: {c['text']}; }}
        QWidget {{ font-family: 'Microsoft YaHei UI'; font-size: 13px; }}
        QLabel {{ color: {c['text']}; }}
        QWidget#instructionEditorBody {{ background: {c['bg']}; color: {c['text']}; }}
        QDockWidget[instructionParameter="true"], QScrollArea#parameterScroll,
        QWidget#parameterViewport {{ background: {c['bg']}; color: {c['text']}; border: none; }}
        QWidget#tab, QWidget#editorView, QWidget#multifunctionView,
        QWidget#beginnerView, QStackedWidget {{ background: {c['bg']}; color: {c['text']}; }}
        QMenuBar, QMenu, QToolBar {{ background: {c['nav']}; color: {c['text']}; border-color: {c['line']}; spacing: 4px; }}
        QMenu {{ background: {c['surface']}; color: {c['text']}; border: 1px solid {c['line']}; border-radius: 10px; padding: 4px; font-size: 12px; }}
        QMenu::item {{ padding: 3px 18px 3px 20px; margin: 0; border: none; border-radius: 5px; font-size: 12px; }}
        QMenu::item:disabled {{ color: {c['dim']}; background: transparent; }}
        QMenu::separator {{ height: 1px; background: {c['line']}; margin: 3px 7px; }}
        QMenuBar::item:selected, QMenu::item:selected {{ background: {c['surface3']}; color: {c['accent']}; }}
        QToolBar {{ border-bottom: 1px solid {c['line']}; padding: 0px 2px; spacing: 2px; font-size: 11px; }}
        QToolBar QToolButton {{ padding: 2px 5px; border-radius: 4px; font-size: 11px; }}
        QToolBar QToolButton:hover {{ background: {c['surface3']}; color: {c['accent']}; }}
        QTabWidget::pane {{ border: none; background: {c['bg']}; top: 0px; }}
        QTabWidget#workspaceTabs {{ background: {c["bg"]}; }}
        QTabWidget#workspaceTabs::pane {{ border: none; padding: 0px; margin: 0px; top: 0px; }}
        QWidget#multifunctionView {{ background: {c['surface']}; }}
        QTabBar::tab {{ background: {c['surface']}; color: {c['dim']}; padding: 4px 12px; border: 1px solid {c['line']}; border-radius: 8px; margin: 2px; }}
        QTabBar::tab:selected {{ background: {c['accent']}; color: {c['accent_text']}; font-weight: 700; }}
        QTabBar::tab:hover:!selected {{ background: {c['surface3']}; color: {c['accent']}; }}
        QWidget#instructionPaletteHost, QGroupBox#groupBox_3 {{ background: {c['surface']}; color: {c['text']}; border: none; border-radius: 12px; }}
        QGroupBox#groupBox_3 {{ margin-top: 0px; padding-top: 20px; }}
        QWidget#instructionTreeSurface {{ background: {c['surface2']}; border: none; border-radius: 12px; }}
        QTreeWidget#instructionTree {{ border: none; background: transparent; }}
        QGroupBox#groupBox_3::title {{ color: {c['text']}; subcontrol-origin: border; subcontrol-position: top left; top: 6px; left: 12px; padding: 0px; }}
        QWidget#instructionPaletteHost QTreeWidget, QWidget#instructionPaletteHost QLineEdit,
        QGroupBox#groupBox_3 QTextEdit {{ background: {c['surface2']}; color: {c['text']}; }}
        QTreeWidget#instructionTree::item {{ color: {c['text']}; padding: 5px; border: 1px solid transparent; border-radius: 5px; }}
        QTreeWidget#instructionTree::item:hover:!selected {{ background: {c['surface3']}; border-color: {c['accent']}; }}
        QTreeWidget#instructionTree::item:selected {{ background: {c['accent2']}; color: white; border-color: {c['accent']}; }}
        QFrame#viewNavigation {{ background: {c['nav']}; border: 1px solid {c['line']}; border-radius: 12px; min-width: 175px; max-width: 220px; }}
        QLabel#homePageTitle {{ color: {c['text']}; font-size: 17px; font-weight: 700; padding: 0px; }}
        QLabel#navTitle, QLabel#pageTitle {{ color: {c['text']}; font-size: 17px; font-weight: 700; padding: 8px; }}
        QListWidget#beginnerNavigation {{ background: transparent; border: none; outline: none; }}
        QListWidget#beginnerNavigation::item {{ color: {c['text']}; padding: 11px 14px; margin: 1px 0; }}
        QListWidget#beginnerNavigation::item:selected {{ background: {c['accent']}; color: {c['accent_text']}; border-radius: 8px; }}
        QListWidget#beginnerNavigation::item:hover:!selected {{ background: {c['surface3']}; color: {c['accent']}; }}
        QFrame#contentCard {{ background: {c['surface']}; border: 1px solid {c['line']}; border-radius: 12px; padding: 12px; }}
        QFrame#workspacePanel {{ background: {c['surface']}; border: none; border-radius: 12px; }}
        QFrame#workspacePanel[attachedToNavigation="true"] {{ border-top-left-radius: 0px; }}
        QLabel#cardTitle {{ color: {c['text']}; font-size: 18px; font-weight: 700; padding: 4px; }}
        QLabel#sectionTitle {{ color: {c['text']}; font-size: 15px; font-weight: 700; padding: 2px 4px 7px 4px; }}
        QLabel#mutedText {{ color: {c['dim']}; padding: 3px; }}
        QWidget[compactRecording="true"] QFrame#recordingControls {{ background: {c['surface']}; border: none; border-radius: 6px; }}
        QWidget[compactRecording="true"] QLabel#pageTitle {{ padding: 0px 2px; font-size: 14px; }}
        QWidget[compactRecording="true"] QPushButton {{ padding: 4px 8px; border-radius: 6px; }}
        QWidget[compactRecording="true"] QSpinBox, QWidget[compactRecording="true"] QDoubleSpinBox,
        QWidget[compactRecording="true"] QLineEdit {{ padding: 3px 6px; min-height: 22px; }}
        QWidget[compactRecording="true"] QLabel#taskStats {{ padding: 5px 8px; font-size: 13px; border-radius: 6px; }}
        QLabel#taskStats {{ color: {c['text']}; background: {c['surface2']}; border-radius: 10px; padding: 14px; font-size: 15px; }}
        QWidget#flowTips {{ background: {c['surface']}; border: none; }}
        QLabel#flowTipBadge {{ color: {c['accent']}; font-size: 12px; font-weight: 600; }}
        QLabel#flowTipText, QLabel#flowTipCounter {{ color: {c['dim']}; font-size: 12px; padding: 0px; }}
        QWidget#flowTips QToolButton {{ padding: 0px; border: none; border-radius: 4px; font-size: 18px; background: transparent; }}
        QWidget#flowTips QToolButton:hover {{ background: {c['surface3']}; color: {c['accent']}; }}
        QPushButton, QToolButton {{ background: {c['surface2']}; color: {c['text']}; border: 1px solid {c['line']}; border-radius: 8px; padding: 7px 12px; }}
        QTabBar QToolButton {{ padding: 0px; border-radius: 4px; }}
        QPushButton:hover, QToolButton:hover {{ background: {c['surface3']}; color: {c['accent']}; border-color: {c['accent']}; }}
        QPushButton:pressed {{ background: {c['accent2']}; color: white; }}
        QPushButton:disabled, QToolButton:disabled {{ background: {c['surface']}; color: {c['dim']}; border-color: {c['line']}; }}
        QPushButton#accentButton {{ background: {c['accent']}; color: {c['accent_text']}; font-weight: 700; border-color: {c['accent']}; }}
        QSlider#imageConfidenceSlider::groove:horizontal {{ height: 5px; background: {c['surface3']}; border-radius: 2px; }}
        QSlider#imageConfidenceSlider::sub-page:horizontal {{ background: {c['accent']}; border-radius: 2px; }}
        QSlider#imageConfidenceSlider::handle:horizontal {{ width: 14px; margin: -5px 0; border-radius: 7px; background: {c['accent']}; }}
        QPushButton#dangerButton {{ background: {c['danger']}; color: white; font-weight: 700; border-color: {c['danger']}; }}
        QLineEdit, QPlainTextEdit, QTextEdit, QSpinBox, QDoubleSpinBox, QComboBox {{ background: {c['surface2']}; color: {c['text']}; border: 1px solid {c['line']}; border-radius: 8px; padding: 6px; selection-background-color: {c['accent2']}; }}
        QLineEdit#instructionSearchEdit {{ padding: 1px 6px; min-height: 0px; border-radius: 4px; }}
        QSpinBox, QDoubleSpinBox {{ min-height: 20px; padding: 6px 20px 6px 6px; }}
        QSpinBox QLineEdit, QDoubleSpinBox QLineEdit {{ border: none; border-radius: 0; padding: 0; min-height: 0; background: transparent; }}
        QSpinBox::up-button, QDoubleSpinBox::up-button {{ subcontrol-origin: border; subcontrol-position: top right; width: 18px; height: 16px; border: none; }}
        QSpinBox::down-button, QDoubleSpinBox::down-button {{ subcontrol-origin: border; subcontrol-position: bottom right; width: 18px; height: 16px; border: none; }}
        QLineEdit:focus, QPlainTextEdit:focus, QTextEdit:focus, QSpinBox:focus, QDoubleSpinBox:focus, QComboBox:focus {{ border-color: {c['accent']}; }}
        QComboBox::drop-down {{ border: none; width: 24px; }}
        QComboBox {{ padding-right: 28px; }}
        QComboBox::down-arrow, QSpinBox::down-arrow, QDoubleSpinBox::down-arrow {{ image: url("{down_arrow}"); width: 12px; height: 12px; }}
        QSpinBox::up-arrow, QDoubleSpinBox::up-arrow {{ image: url("{up_arrow}"); width: 12px; height: 12px; }}
        QCheckBox, QRadioButton {{ color: {c['text']}; spacing: 7px; padding: 3px; }}
        QCheckBox::indicator, QRadioButton::indicator {{ width: 16px; height: 16px; }}
        QCheckBox::indicator:unchecked, QRadioButton::indicator:unchecked {{ background: {c['surface2']}; border: 1px solid {c['line']}; border-radius: 5px; }}
        QCheckBox::indicator:checked, QRadioButton::indicator:checked {{ background: {c['accent']}; border: 2px solid {c['surface2']}; border-radius: 5px; }}
        QAbstractScrollArea, QAbstractScrollArea QWidget#qt_scrollarea_viewport,
        QTableWidget, QListWidget {{ background: {c['surface']}; color: {c['text']}; alternate-background-color: {c['surface2']}; border: 1px solid {c['line']}; border-radius: 10px; gridline-color: {c['line']}; }}
        QTableWidget#commandTable {{ background-color: {c['surface']}; alternate-background-color: {c['surface2']}; border: none; }}
        QTableWidget#commandTable::item {{ border: none; padding: 5px; }}
        QTableWidget#commandTable::item:hover:!selected {{ border-bottom: 1px solid {c['accent']}; }}
        QTextEdit#textEdit {{ background: {c['nav']}; color: {c['text']}; border: none; border-radius: 10px; padding: 8px; }}
        QTableWidget#commandTable::item:selected, QTableWidget#commandTable::item:selected:alternate {{ background-color: {c['accent2']}; color: white; }}
        QTableWidget::item:selected, QListWidget::item:selected {{ background: {c['accent2']}; color: white; }}
        QHeaderView {{ background: {c['surface2']}; color: {c['accent']}; }}
        QHeaderView::section {{ background: {c['surface2']}; color: {c['accent']}; border: none; border-right: 1px solid {c['line']}; padding: 7px; font-weight: 700; }}
        QTableCornerButton::section, QAbstractScrollArea::corner {{ background: {c['surface2']}; border: none; border-right: 1px solid {c['line']}; border-bottom: 1px solid {c['line']}; }}
        QToolTip {{ background: {c['surface3']}; color: {c['text']}; border: 1px solid {c['line']}; border-radius: 6px; padding: 5px; }}
        QDialog {{ background: {c['bg']}; color: {c['text']}; }}
        QDialogButtonBox QPushButton {{ min-width: 76px; }}
        QScrollBar:vertical {{ background: {c['bg']}; width: 11px; }}
        QScrollBar::handle:vertical {{ background: {c['surface3']}; min-height: 24px; border-radius: 5px; }}
        QScrollBar::handle:vertical:hover {{ background: {c['accent2']}; }}
        QScrollBar::add-page:vertical, QScrollBar::sub-page:vertical {{ background: {c['bg']}; }}
        QScrollBar:horizontal {{ background: {c['bg']}; height: 11px; }}
        QScrollBar::handle:horizontal {{ background: {c['surface3']}; min-width: 24px; border-radius: 5px; }}
        QScrollBar::add-page:horizontal, QScrollBar::sub-page:horizontal {{ background: {c['bg']}; }}
        QScrollBar::add-line, QScrollBar::sub-line {{ width: 0px; height: 0px; }}
        QFrame#recordingOptionSeparator {{ background: {c['line']}; border: none; }}
        QSplitter::handle {{ background: transparent; }}
        QSplitter::handle:horizontal {{ border: none; background: transparent; margin: 0px; }}
        QSplitter::handle:vertical {{ border: none; background: transparent; margin: 0px; }}
        QSplitter::handle:horizontal:hover {{ border: none; background: transparent; }}
        QSplitter::handle:vertical:hover {{ border: none; background: transparent; }}

        QScrollArea#homeWorkspace, QScrollArea#homeWorkspace > QWidget {{ border: none; background: {c['bg']}; }}
        QPushButton#homeEntry {{ text-align: left; padding: 12px 16px; line-height: 1.6; }}
        QListWidget#homeRecentProjects {{ border: none; background: transparent; }}
        QListWidget#homeRecentProjects::item {{ padding: 8px 10px; border-radius: 6px; }}
        QWidget#mainWorkspacePage {{ background: {c['bg']}; border: none; }}
        QScrollArea#controlsScroll, QWidget#controlsScrollViewport {{ background: {c['bg']}; border: none; }}
        QStatusBar {{ background: {c['bg']}; color: {c['dim']}; border: none; padding: 0px 6px; }}
        QStatusBar::item {{ border: none; }}
        QStatusBar QSizeGrip {{ background: transparent; }}
        QGroupBox {{ color: {c['accent']}; background: {c['surface']}; border: 1px solid {c['line']}; border-radius: 10px; margin-top: 10px; padding-top: 10px; font-weight: 700; }}
        QGroupBox::title {{ subcontrol-origin: margin; left: 10px; padding: 0 5px; }}
    """)
    QTimer.singleShot(0, self._align_search_row)
