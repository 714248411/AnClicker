"""Content-sized instruction settings without vertical filler between sections."""
from qt_compat.QtCore import Qt, QSize
from qt_compat.QtWidgets import QWidget, QVBoxLayout, QLabel, QSizePolicy


def compact_body(body):
    layout = body.layout()
    if layout is None:
        return
    for box in [layout] + body.findChildren(QVBoxLayout):
        if not isinstance(box, QVBoxLayout):
            continue
        box.setAlignment(Qt.AlignTop)
        box.setSpacing(8)
        for index in range(box.count()-1, -1, -1):
            item = box.itemAt(index)
            spacer = item.spacerItem()
            if spacer is not None and spacer.expandingDirections() & Qt.Vertical:
                box.takeAt(index)
            else:
                box.setStretch(index, 0)
    # Explanatory labels should occupy their text height, never consume spare space.
    for label in body.findChildren(QLabel):
        if label.pixmap() is None or label.pixmap().isNull():
            policy = label.sizePolicy()
            policy.setVerticalPolicy(QSizePolicy.Fixed)
            label.setSizePolicy(policy)
    layout.invalidate()
    layout.activate()


def parameter_popup_size(editor):
    body = getattr(editor, '_parameter_body', None)
    if body is None:
        return QSize(editor.size().expandedTo(editor.sizeHint()))
    compact_body(body)
    heading = body.findChild(QLabel, 'titleLabel')
    hidden = heading.isHidden() if heading else True
    if heading is not None:
        heading.hide()
    layout = body.layout()
    layout.invalidate()
    layout.activate()
    width = max(480, min(760, editor.width()))
    content_width = width - 32
    height = layout.totalHeightForWidth(content_width) if layout.hasHeightForWidth() else layout.sizeHint().height()
    if heading is not None:
        heading.setVisible(not hidden)
    available = editor.screen().availableGeometry()
    return QSize(min(width, available.width()-40), min(max(200, height+56), available.height()-60))


def fit_initial_popup(editor, dock):
    if not dock.isVisible() or not dock.isFloating():
        return
    editor._panel_scaler.apply()
    size = parameter_popup_size(editor)
    dock.resize(size)
    editor._original_popup_size = size
