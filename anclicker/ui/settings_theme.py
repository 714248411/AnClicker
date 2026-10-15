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
    workspace = getattr(window, 'view_workspace', None)
    if workspace is None:
        return
    style_settings_combos = _module_imports.load('style_settings_combos')
    style_settings_combos(dialog, window)
    c = workspace.THEMES[workspace.theme_mode]
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
    dialog.setStyleSheet(f"""
        QDialog {{ font-size:14px; background: {c['surface']}; color: {c['text']}; }}
        QLabel, QCheckBox {{ color: {c['text']}; background: transparent; }}
        QLabel#settingsHint {{ color: {c['dim']}; font-size: 11px; }}
        QWidget#settingsBody, QWidget#settingsViewport, QWidget#settingsRow {{ background: {c['surface']}; color: {c['text']}; }}
        QScrollArea#settingsScroll {{ background: {c['surface']}; border: 1px solid {c['line']}; border-radius: 10px; padding: 6px; }}
        QLineEdit, QSpinBox, QDoubleSpinBox, QComboBox {{ background: {c['surface2']}; color: {c['text']};
            border: 1px solid {c['line']}; border-radius: 6px; padding: 5px 8px; }}
        QLineEdit:focus {{ border-color: {c['accent']}; }}
        QPushButton {{ background: {c['surface2']}; color: {c['text']}; border: 1px solid {c['line']};
            border-radius: 6px; padding: 5px 12px; }}
        QPushButton:hover {{ background: {c['surface3']}; border-color: {c['accent']}; }}
        QPushButton#settingsSave {{ background: {c['accent']}; color: {c['accent_text']}; border-color: {c['accent']}; }}
        QCheckBox {{ spacing: 6px; padding: 2px; }}
    """)

    # Scroll-area contents can retain the platform Base/Window brush on Qt 5.
    # Apply the palette directly and explicitly enable styled container painting.
    for widget in dialog.findChildren(QWidget):
        widget.setPalette(palette)
        if widget.objectName() in ('settingsBody', 'settingsViewport', 'settingsRow'):
            widget.setBackgroundRole(QPalette.ColorRole.Window)
            widget.setAutoFillBackground(True)
            widget.setAttribute(Qt.WidgetAttribute.WA_StyledBackground, True)
            widget.setStyleSheet(
                f"QWidget#{widget.objectName()} {{ background-color: {c['surface']}; "
                f"color: {c['text']}; border: none; }}")
