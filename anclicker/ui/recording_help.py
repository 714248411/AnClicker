"""Compact recording title with an accessible book-shaped help button."""
from html import escape
from anclicker.platform.qt_compat.QtCore import Qt, QSize
from anclicker.platform.qt_compat.QtGui import QIcon, QPixmap, QPainter, QColor, QPen
from anclicker.platform.qt_compat.QtWidgets import (QHBoxLayout, QVBoxLayout, QLabel, QToolButton,
                                 QDialog, QTextBrowser, QDialogButtonBox)

from anclicker._imports import DeferredImports as _DeferredImports

# Dependencies declared here retain their existing on-demand loading boundaries.
_module_imports = _DeferredImports(globals(), {
    'apply_settings_theme': ('from', 'anclicker.ui.settings_theme', ('apply_settings_theme',), 0),
})



def recording_header(parent, title, description):
    row = QHBoxLayout()
    row.setContentsMargins(0, 0, 0, 0)
    row.setSpacing(4)
    label = QLabel(title, parent)
    label.setObjectName('pageTitle')
    row.addWidget(label)
    book = QToolButton(parent)
    book.setObjectName('recordingHelpBook')
    book.setFixedSize(26, 26)
    book.setIconSize(QSize(18, 18))
    book.setCursor(Qt.CursorShape.WhatsThisCursor)
    book.setAccessibleName(title + '使用说明')
    book.setAccessibleDescription(description)
    pixmap = QPixmap(36, 36)
    pixmap.setDevicePixelRatio(2)
    pixmap.fill(Qt.GlobalColor.transparent)
    painter = QPainter(pixmap)
    painter.setRenderHint(QPainter.RenderHint.Antialiasing)
    painter.setPen(QPen(QColor('#438bd1'), 1.3))
    painter.drawRoundedRect(2, 3, 14, 12, 2, 2)
    painter.drawLine(9, 3, 9, 15)
    for y in (6, 9, 12):
        painter.drawLine(4, y, 7, y)
        painter.drawLine(11, y, 14, y)
    painter.end()
    book.setIcon(QIcon(pixmap))
    book.setStyleSheet('QToolButton#recordingHelpBook {border:none; padding:2px; background:transparent; border-radius:4px;} QToolButton#recordingHelpBook:hover {background:rgba(67,139,209,28);}')
    summary = description.split('\n\n', 1)[0]
    text = ('<div style="max-width:360px"><b>' + escape(title) + '使用说明</b><br><br>'
            + escape(summary).replace('\n', '<br>') + '<br><br>点击小书本查看完整说明。</div>')
    book.setToolTip(text)
    book.setToolTipDuration(30000)

    def show_help():
        dialog = QDialog(parent)
        dialog.setWindowTitle(title + '使用说明')
        dialog.setWindowFlag(Qt.WindowType.WindowContextHelpButtonHint, False)
        dialog.resize(620, 560)
        layout = QVBoxLayout(dialog)
        layout.setContentsMargins(14, 12, 14, 12)
        browser = QTextBrowser(dialog)
        browser.setReadOnly(True)
        browser.setOpenExternalLinks(False)
        sections = []
        for section in description.split('\n\n'):
            heading, _, content = section.partition('\n')
            sections.append('<p><b>' + escape(heading) + '</b><br>'
                            + escape(content).replace('\n', '<br>') + '</p>')
        browser.setHtml(''.join(sections))
        layout.addWidget(browser, 1)
        buttons = QDialogButtonBox(QDialogButtonBox.StandardButton.Close, dialog)
        buttons.button(QDialogButtonBox.StandardButton.Close).setText('关闭')
        buttons.rejected.connect(dialog.reject)
        layout.addWidget(buttons)
        apply_settings_theme = _module_imports.load('apply_settings_theme')
        window = getattr(parent, 'window', None)
        apply_settings_theme(dialog, window)
        workspace = getattr(window, 'view_workspace', None)
        if workspace is not None:
            c = workspace.THEMES[workspace.theme_mode]
            browser.setStyleSheet(f"QTextBrowser {{ background: {c['surface']}; color: {c['text']}; "
                                 f"border: 1px solid {c['line']}; border-radius: 8px; padding: 10px; }}")
        dialog.exec()

    book.clicked.connect(show_help)
    row.addWidget(book, 0, Qt.AlignmentFlag.AlignVCenter)
    row.addStretch(1)
    return row
