"""Content-sized instruction settings without vertical filler between sections."""
from anclicker.platform.qt_compat.QtCore import Qt, QSize, QRect
from anclicker.platform.qt_compat.QtWidgets import QWidget, QVBoxLayout, QLabel, QSizePolicy


def compact_body(body):
    layout = body.layout()
    if layout is None:
        return
    for box in [layout] + body.findChildren(QVBoxLayout):
        if not isinstance(box, QVBoxLayout) or box.property("preserveVerticalStretch"):
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


def centered_popup_geometry(content, main_rect, available):
    max_height = max(1, min(int(main_rect.height()*1.5), available.height()))
    width = max(1, min(content.width(), available.width()))
    height = max(1, min(content.height(), max_height))
    x = main_rect.center().x() - width//2
    y = main_rect.center().y() - height//2
    x = max(available.left(), min(x, available.right()-width+1))
    y = max(available.top(), min(y, available.bottom()-height+1))
    return QRect(x, y, width, height)


def fit_initial_popup(editor, dock):
    if not dock.isVisible() or not dock.isFloating():
        return
    owner = getattr(editor, '_workspace_owner', None) or dock.parentWidget() or editor
    available = (owner.screen() or dock.screen()).availableGeometry()
    scaler = getattr(editor, '_panel_scaler', None)
    if scaler is not None:
        scaler.expanded_pixels = 14
        scaler.last_size = None
        scaler.apply()
    size = parameter_popup_size(editor)
    if getattr(editor, '_parameter_body', None) is None and editor.layout() is not None:
        layout = editor.layout()
        width = min(max(480, editor.sizeHint().width(), editor.width()), 900, available.width())
        height = layout.totalHeightForWidth(width-24) if layout.hasHeightForWidth() else layout.sizeHint().height()
        size = QSize(width, max(160, height+32))
    chrome = max(0, dock.height()-dock.widget().height()) if dock.widget() else 0
    size.setHeight(size.height()+chrome)
    geometry = centered_popup_geometry(size, owner.frameGeometry(), available)
    dock.setMinimumSize(0, 0)
    dock.setMaximumHeight(max(1, min(int(owner.frameGeometry().height()*1.5), available.height())))
    dock.resize(geometry.size())
    dock.move(geometry.topLeft())
    editor._original_popup_size = geometry.size()
    if scaler is not None:
        if hasattr(scaler, 'expanded_pixels'): del scaler.expanded_pixels
        scaler.reference_width = max(1, scaler.viewport.width())
        scaler.reference_height = max(1, scaler.viewport.height())
        scaler.last_size = None
        scaler.apply()
