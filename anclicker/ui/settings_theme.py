"""Theme standard settings dialogs using the active workspace colors."""
from anclicker.platform.qt_compat.QtCore import Qt
from anclicker.platform.qt_compat.QtGui import QPalette, QColor
from anclicker.platform.qt_compat.QtWidgets import QWidget

from anclicker._imports import DeferredImports as _DeferredImports

# Dependencies declared here retain their existing on-demand loading boundaries.
_module_imports = _DeferredImports(globals(), {
    'style_settings_combos': ('from', 'anclicker.ui.settings_combo', ('style_settings_combos',), 0),
})



def apply_settings_theme(dialog, window):
    from anclicker.ui.window_edges import install_window_edges, apply_window_edges
    install_window_edges()
    dialog._edge_workspace=getattr(window,'view_workspace',None)
    apply_window_edges(dialog,window)
    workspace = getattr(window, 'view_workspace', None)
    if workspace is None:
        return
    style_settings_combos = _module_imports.load('style_settings_combos')
    style_settings_combos(dialog, window)
    c = workspace.THEMES[workspace.theme_mode]
    if hasattr(dialog,'titleBar') and hasattr(dialog.titleBar,'apply_theme'):
        dialog.titleBar.apply_theme(c)
        dialog.outline.color=QColor(c['line']);dialog.outline.update()
    palette = dialog.palette()
    for role, color in (
        (QPalette.ColorRole.Window, c['surface']),
        (QPalette.ColorRole.Base, c['surface']),
        (QPalette.ColorRole.AlternateBase, c['surface2']),
        (QPalette.ColorRole.WindowText, c['text']),
        (QPalette.ColorRole.Text, c['text']),
        (QPalette.ColorRole.Button, c['surface2']),
        (QPalette.ColorRole.ButtonText, c['text']),
        (QPalette.ColorRole.Highlight, c['accent']),
        (QPalette.ColorRole.HighlightedText, c['accent_text']),
        (QPalette.ColorRole.PlaceholderText, c['dim']),
    ):
        palette.setColor(role, QColor(color))
    dialog.setPalette(palette)
    dialog.setAutoFillBackground(True)
    dialog.setAttribute(Qt.WidgetAttribute.WA_StyledBackground, True)
    dialog.setStyleSheet(f"""
        QWidget {{ font-size:14px; }}
        QDialog, QWidget#InstructionEditor {{ font-size:14px; background: {c['surface']}; color: {c['text']}; }}
        QLabel, QCheckBox {{ color: {c['text']}; background: transparent; }}
        QLabel#settingsHint {{ color: {c['dim']}; font-size: 14px; }}
        QWidget#settingsBody, QWidget#settingsViewport, QWidget#settingsRow, QWidget#instructionEditorBody, QWidget#imageClickWorkspace, QWidget#parameterViewport {{ background: {c['surface']}; color: {c['text']}; }}
        QScrollArea#settingsScroll {{ background: {c['surface']}; border: 1px solid {c['line']}; border-radius: 10px; padding: 6px; }}
        QTabWidget::pane {{background:{c['surface']};border:none;top:0px;}}
        QStackedWidget {{background:{c['surface']};border:none;}}
        QScrollArea#parameterScroll {{background:{c['surface']};border:none;}} 
        QTabBar::tab {{background:{c['surface2']};color:{c['text']};border:1px solid {c['line']};border-radius:6px;padding:5px 10px;margin-right:4px;margin-bottom:4px;}}
        QTabBar::tab:selected {{background:{c['accent']};color:{c['accent_text']};border-color:{c['accent']};}}
        QGroupBox {{color:{c['text']};border:1px solid {c['line']};border-radius:7px;margin-top:12px;padding-top:8px;}}
        QGroupBox::title {{subcontrol-origin:margin;left:10px;padding:0 4px;color:{c['accent']};}}
        QLineEdit, QSpinBox, QDoubleSpinBox, QComboBox, QKeySequenceEdit, QPlainTextEdit, QTextEdit, QAbstractItemView {{ background: {c['surface2']}; color: {c['text']};
            border: 1px solid {c['line']}; border-radius: 6px; padding: 5px 8px; }}
        QSpinBox QLineEdit, QDoubleSpinBox QLineEdit {{ border:none; border-radius:0; padding:0; min-height:0; background:transparent; }}
        QLineEdit:focus {{ border-color: {c['accent']}; }}
        QPushButton {{ background: {c['surface2']}; color: {c['text']}; border: 1px solid {c['line']};
            border-radius: 6px; padding: 5px 12px; }}
        QPushButton:hover {{ background: {c['surface3']}; border-color: {c['accent']}; }}
        QPushButton#settingsSave {{ background: {c['accent']}; color: {c['accent_text']}; border-color: {c['accent']}; }}
        QCheckBox {{ spacing: 6px; padding: 2px; }}
        QLineEdit:disabled, QSpinBox:disabled, QDoubleSpinBox:disabled, QComboBox:disabled,
        QPushButton:disabled {{ color:{c['dim']}; background:{c['surface2']}; border-color:{c['line']}; }}
        QAbstractItemView {{ selection-background-color:{c['accent']}; selection-color:{c['accent_text']}; }}
        QHeaderView::section {{ background:{c['surface2']}; color:{c['text']}; border:1px solid {c['line']}; padding:5px; }}
        QTableWidget {{ gridline-color:{c['line']}; alternate-background-color:{c['surface']}; }}
        QTableCornerButton::section {{ background:{c['surface2']}; border:1px solid {c['line']}; }}
        QScrollBar:vertical {{ background:{c['surface']}; width:10px; margin:0; }}
        QScrollBar::handle:vertical {{ background:{c['line']}; min-height:24px; border-radius:4px; }}
        QScrollBar::add-line:vertical, QScrollBar::sub-line:vertical {{ height:0; }}
        QScrollBar::add-page:vertical, QScrollBar::sub-page:vertical {{ background:transparent; }}
        QScrollBar:horizontal {{ background:{c['surface']}; height:10px; margin:0; }}
        QScrollBar::handle:horizontal {{ background:{c['line']}; min-width:24px; border-radius:4px; }}
        QScrollBar::add-line:horizontal, QScrollBar::sub-line:horizontal {{ width:0; }}
        QScrollBar::add-page:horizontal, QScrollBar::sub-page:horizontal {{ background:transparent; }}
    """)

    # Scroll-area contents can retain the platform Base/Window brush on Qt 5.
    # Apply the palette directly and explicitly enable styled container painting.
    for widget in dialog.findChildren(QWidget):
        if dialog.property('uniformSettingsFont'):
            import re
            from anclicker.ui.interface_scale import original_style
            base = re.sub(r'font-size\s*:\s*\d+(?:\.\d+)?(?:px|pt)', 'font-size:14px', original_style(widget))
            widget._interface_style = (base, base)
            if widget.styleSheet() != base: widget.setStyleSheet(base)
        widget.setPalette(palette)
        if widget.objectName() in ('settingsBody', 'settingsViewport', 'settingsRow', 'instructionEditorBody', 'imageClickWorkspace', 'parameterViewport'):
            widget.setBackgroundRole(QPalette.ColorRole.Window)
            widget.setAutoFillBackground(True)
            widget.setAttribute(Qt.WidgetAttribute.WA_StyledBackground, True)
            widget.setStyleSheet(
                f"QWidget#{widget.objectName()} {{ background-color: {c['surface']}; "
                f"color: {c['text']}; border: none; }}")


def fit_window_settings(editor):
    """Keep sparse forms at the top and let long labels wrap in narrow panels."""
    from anclicker.platform.qt_compat.QtWidgets import QFormLayout, QVBoxLayout, QLabel, QPushButton
    root = editor.layout()
    if root is not None:
        root.setAlignment(Qt.AlignTop)
        root.setContentsMargins(10, 10, 10, 10)
        root.setSpacing(8)
    for form in editor.findChildren(QFormLayout):
        form.setRowWrapPolicy(QFormLayout.WrapLongRows)
        form.setFieldGrowthPolicy(QFormLayout.AllNonFixedFieldsGrow)
        form.setFormAlignment(Qt.AlignTop)
        form.setVerticalSpacing(6)
        form.setHorizontalSpacing(8)
    for layout in editor.findChildren(QVBoxLayout):
        layout.setAlignment(Qt.AlignTop)
    for label in editor.findChildren(QLabel):
        if label.pixmap() is None and label.text():
            label.setWordWrap(True)
    for button in editor.findChildren(QPushButton):
        button.setMinimumHeight(30)
