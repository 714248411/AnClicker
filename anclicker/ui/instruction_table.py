"""Linked Clicker workspaces and the light/dark desktop themes."""
from __future__ import annotations
import weakref
from time import monotonic
import json
from anclicker.platform.qt_compat.QtCore import QObject, QEvent, QTimer, QSignalBlocker, Signal, Qt, QMimeData, QItemSelectionModel, QPoint
from anclicker.platform.qt_compat.QtGui import QColor, QKeySequence, QPalette, QDrag, QPainter, QPen, QPolygon
from anclicker.platform.qt_compat.QtWidgets import QAbstractItemView, QApplication, QFrame, QHBoxLayout, QHeaderView, QLabel, QMenu, QMessageBox, QSplitter, QSizePolicy, QTableWidget, QStyledItemDelegate, QStyle, QTableWidgetItem, QVBoxLayout, QStyleOptionViewItem, QToolTip
from anclicker.ui.node_editor.palette import INSTRUCTION_MIME_TYPE
from anclicker.ui.log_actions import configure_log_actions
from anclicker.ui.fold_lock_icon import paint_fold_lock
from anclicker.ui.instruction_menu import add_instruction_categories
from anclicker.ui.instruction_clipboard import set_command_mime, command_clipboard_data
from anclicker.ui.two_column_menu import MenuColumn, exec_two_column_menu
from anclicker.ui.drag_feedback import FeedbackOverlay, HoverExpandController, animation_menu, animation_policy, visual_only, feedback_call
from anclicker.platform.qt_compat.QtCore import QRectF
from anclicker.ui.instruction_thumbnails import VARIABLE, THUMBNAIL_ROLE, ThumbnailCache, image_references, thumbnail_layout

from anclicker._imports import DeferredImports as _DeferredImports

# Dependencies declared here retain their existing on-demand loading boundaries.
_module_imports = _DeferredImports(globals(), {
    'connected_fold_ranges': ('from', 'anclicker.domain.flow_comments', ('connected_fold_ranges',), 0),
    'loop_groups': ('from', 'anclicker.domain.flow_loop_table', ('loop_groups',), 0),
    'style_context_menu': ('from', 'anclicker.ui.context_menu_style', ('style_context_menu',), 0),
    'snapshot_disabled_ids': ('from', 'anclicker.domain.flow_comments', ('snapshot_disabled_ids',), 0),
    'asdict': ('from', 'dataclasses', ('asdict',), 0),
    'InstructionDraft': ('from', 'anclicker.domain.instructions', ('InstructionDraft',), 0),
    'QTableWidgetSelectionRange': ('from', 'anclicker.platform.qt_compat.QtWidgets', ('QTableWidgetSelectionRange',), 0),
})


LOCK_DRAG_DWELL_MS = 5000


class NavigationHeaderHeight(QObject):
    def __init__(self, workspace):
        super().__init__(workspace.command_table)
        self.workspace = workspace
        self.timer = QTimer(self)
        self.timer.setSingleShot(True)
        self.timer.timeout.connect(self.sync)
        self.tabbar = workspace.tabs.tabBar()
        self.tabbar.installEventFilter(self)
        workspace.command_table.horizontalHeader().installEventFilter(self)
        self.timer.start(0)

    def eventFilter(self, watched, event):
        if event.type() in (QEvent.Show, QEvent.FontChange, QEvent.StyleChange, QEvent.LayoutRequest) or (watched is self.tabbar and event.type() == QEvent.Resize):
            self.timer.start(0)
        return False

    def sync(self):
        height = self.tabbar.height() if self.tabbar.isVisible() else self.tabbar.sizeHint().height()
        header = self.workspace.command_table.horizontalHeader()
        # Keep room for glyphs and section padding as the interface font changes.
        height = max(height + 6, header.sizeHint().height(), header.fontMetrics().height() + 12) - 2
        if header.height() != height:
            header.setFixedHeight(height)


FOLD_LOCK_ROLE = int(Qt.ItemDataRole.UserRole) + 17
INDENT_DEPTH_ROLE = int(Qt.ItemDataRole.UserRole) + 19


def command_indent_width(metrics, depth):
    # Two Latin character widths per level; do not depend on space glyph widths.
    return metrics.horizontalAdvance('MM') * max(0, int(depth or 0))


def fold_lock_rect(rect):
    result = rect.adjusted(0, 3, -3, -3)
    result.setLeft(max(rect.left(), result.right() - 27))
    return result


class CommentRowDelegate(QStyledItemDelegate):
    """Paint comment cells explicitly: stylesheet item backgrounds override roles."""

    def paint(self, painter, option, index):
        depth = index.data(INDENT_DEPTH_ROLE)
        text_option = QStyleOptionViewItem(option)
        if depth:
            # Retain the full cell background/selection behind the indented text.
            background_option = QStyleOptionViewItem(option)
            self.initStyleOption(background_option, index)
            background_option.text = ''
            style = option.widget.style() if option.widget else QApplication.style()
            style.drawControl(QStyle.CE_ItemViewItem, background_option, painter, option.widget)
            background = index.data(Qt.BackgroundRole)
            if background is not None and not option.state & QStyle.State_Selected:
                painter.fillRect(option.rect, background)
            text_option.rect.setLeft(option.rect.left() + command_indent_width(option.fontMetrics, depth))
        locked = index.data(FOLD_LOCK_ROLE)
        if locked is not None:
            text_option.rect.adjust(0, 0, -33, 0)
        if text_option.rect.width() > 0:
            self._paint_cell(painter, text_option, index)
        if locked is None:
            return
        painter.save()
        painter.setClipRect(option.rect)
        paint_fold_lock(painter, fold_lock_rect(option.rect), bool(locked), option.palette, option.font)
        progress = self.parent().lock_progress(index.data(Qt.UserRole))
        if progress is not None:
            lock_rect = fold_lock_rect(option.rect)
            size = min(lock_rect.width(), lock_rect.height()) - 2
            ring = QRectF(lock_rect.center().x() - size / 2, lock_rect.center().y() - size / 2, size, size)
            painter.setRenderHint(QPainter.Antialiasing)
            painter.setPen(QPen(QColor('#657080'), 2))
            painter.drawEllipse(ring)
            painter.setPen(QPen(QColor('#38bdf8'), 2.5))
            painter.drawArc(ring, 90 * 16, -int(360 * 16 * progress))
        painter.restore()

    def helpEvent(self, event, view, option, index):
        locked = index.data(FOLD_LOCK_ROLE)
        if locked is not None and fold_lock_rect(option.rect).contains(event.pos()):
            text = '已锁定：整组移动，只能在组前或组后插入，点击解锁' if locked else '未锁定：仅移动本行，点击锁定整组'
            policy = getattr(view.window(), 'tooltip_policy', None)
            if policy is None or policy.allow(text, view):
                QToolTip.showText(event.globalPos(), text, view)
            else:
                QToolTip.hideText()
            return True
        return super().helpEvent(event, view, option, index)

    def _paint_cell(self, painter, option, index):
        key = index.data(THUMBNAIL_ROLE)
        if key:
            image = self.parent().thumbnail_cache.image(key)
            label, image_rect, badge = thumbnail_layout(option.rect, option.fontMetrics,
                str(index.data() or ''), image, len(key[0]))
            base = QStyleOptionViewItem(option)
            self.initStyleOption(base, index)
            base.text = ''
            style = base.widget.style() if base.widget else QApplication.style()
            style.drawControl(QStyle.CE_ItemViewItem, base, painter, base.widget)
            painter.save()
            painter.setClipRect(option.rect)
            background = index.data(Qt.BackgroundRole)
            selected = bool(option.state & QStyle.State_Selected)
            if background is not None and not selected:painter.fillRect(option.rect, background)
            painter.setFont(option.font)
            foreground = index.data(Qt.ForegroundRole)
            painter.setPen(option.palette.color(QPalette.HighlightedText) if selected else
                (foreground if foreground is not None else option.palette.color(QPalette.Text)))
            text_rect = option.rect.adjusted(5, 0, 0, 0)
            text_rect.setRight(image_rect.left()-5)
            painter.drawText(text_rect, Qt.AlignLeft | Qt.AlignVCenter, label)
            if image_rect.isEmpty():
                painter.restore()
                return
            if image is not None and not image.isNull():
                painter.setRenderHint(QPainter.SmoothPixmapTransform)
                # Fit without distorting or cropping the user's reference image.
                fitted = image.size().scaled(image_rect.size(), Qt.KeepAspectRatio)
                from anclicker.platform.qt_compat.QtCore import QRect
                target = QRect(image_rect.x(), image_rect.y()+(image_rect.height()-fitted.height())//2,
                    fitted.width(), fitted.height())
                painter.drawImage(target, image)
            else:
                painter.drawRect(image_rect.adjusted(0,0,-1,-1))
                text = '…' if image is None else ('变量' if any(VARIABLE.search(r) for r in key[0]) else '缺图')
                painter.drawText(image_rect, Qt.AlignCenter, text)
            if badge:
                badge_rect = option.rect.adjusted(image_rect.right()-option.rect.left()+3, 0, -2, 0)
                painter.drawText(badge_rect, Qt.AlignLeft | Qt.AlignVCenter, '+'+str(len(key[0])-1))
            painter.restore()
            return
        background = index.data(Qt.ItemDataRole.BackgroundRole)
        selected = bool(option.state & QStyle.State_Selected)
        if background is None or selected:
            if index.column() != 2:
                return super().paint(painter, option, index)
            # All command labels use the same inset as the guide-line geometry,
            # including selected and commented rows.
            base = QStyleOptionViewItem(option)
            self.initStyleOption(base, index)
            base.text = ''
            style = base.widget.style() if base.widget else QApplication.style()
            style.drawControl(QStyle.CE_ItemViewItem, base, painter, base.widget)
        painter.save()
        painter.setClipRect(option.rect)
        if background is not None and not selected:
            painter.fillRect(option.rect, background)
        painter.setFont(option.font)
        foreground = index.data(Qt.ItemDataRole.ForegroundRole)
        painter.setPen(option.palette.color(QPalette.HighlightedText) if selected else
                       foreground if foreground is not None else option.palette.color(QPalette.Text))
        rect = option.rect.adjusted(5, 0, -5, 0)
        text = option.fontMetrics.elidedText(str(index.data() or ''), Qt.ElideRight, max(0, rect.width()))
        painter.drawText(rect, Qt.AlignLeft | Qt.AlignVCenter, text)
        painter.restore()

class RowDropIndicator(QFrame):
    """Viewport-clipped insertion marker with inward-facing red arrowheads."""
    def paintEvent(self, event):
        painter = QPainter(self)
        painter.setRenderHint(QPainter.Antialiasing)
        y, right = self.height() // 2, self.width() - 2
        painter.setPen(QPen(QColor('#5b6fdc'), 3))
        painter.drawLine(2, y, right, y)
        painter.setPen(Qt.NoPen)
        painter.setBrush(QColor('#ef4444'))
        painter.drawPolygon(QPolygon([QPoint(2, y-5), QPoint(11, y), QPoint(2, y+5)]))
        painter.drawPolygon(QPolygon([QPoint(right, y-5), QPoint(right-9, y), QPoint(right, y+5)]))
        painter.end()


def command_row_label(commands, ids):
    selected = set(ids)
    rows = [i + 1 for i, command in enumerate(commands) if command.id in selected]
    spans = []
    for row in rows:
        if spans and row == spans[-1][1] + 1:
            spans[-1][1] = row
        else:
            spans.append([row, row])
    return '第 ' + '、'.join(str(a) if a == b else f'{a}–{b}' for a, b in spans) + ' 行'


class InstructionTableWidget(QTableWidget):
    """Command table that accepts instruction MIME drops from the palette."""
    runFromRequested = Signal(object)
    instructionDropped = Signal(str, object)
    deleteRequested = Signal()
    copyRequested = Signal()
    cutRequested = Signal()
    dissolveThreadRequested = Signal(object)
    pasteRequested = Signal()
    pasteRelativeRequested = Signal(str)
    rowsMoved = Signal(object, int)
    moveSelectionRequested = Signal(int)
    stepFoldRequested = Signal(object)
    hoverExpandRequested = Signal(object)
    threadNestedRequested = Signal(object, bool)
    stepLockRequested = Signal(object)
    stepLocksRequested = Signal(object, bool)
    ROW_MIME = 'application/x-anclicker-table-row'

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.setAcceptDrops(True)
        self.setDragDropOverwriteMode(False)
        self.setDropIndicatorShown(False)
        from anclicker.ui.table_header import CommandTableHeader
        self.setHorizontalHeader(CommandTableHeader(self))
        from anclicker.ui.table_edge_resize import TableEdgeResizeGrip
        self.edge_resize_grip = TableEdgeResizeGrip(self)
        self.thumbnail_cache = ThumbnailCache(self)
        self.setItemDelegate(CommentRowDelegate(self))
        self._row_press = None
        self._lock_press = None
        self.runtime_row = -1
        self._expanded_border_runs = []
        self.step_groups = {}
        self.instruction_specs_provider = lambda: {}
        self.comment_ranges = {}
        self.collapsed_comments = set()
        self.loop_ranges = {}
        self.collapsed_loops = set()
        self._fold_click_id = None
        self._ignore_fold_click_until = 0.0
        self._fold_click_timer = QTimer(self)
        self._fold_click_timer.setSingleShot(True)
        self._fold_click_timer.timeout.connect(self._toggle_clicked_fold)
        self.cellClicked.connect(self._queue_fold_click)
        self.cellDoubleClicked.connect(self._on_fold_double_click)
        self._drop_line = RowDropIndicator(self.viewport())
        self._drop_line.setAttribute(Qt.WidgetAttribute.WA_TransparentForMouseEvents)
        self._drop_line.hide()
        self.feedback = FeedbackOverlay(self)
        self.hover_expand = HoverExpandController(self, self._expand_hovered)
        self._hover_point = None
        self._dragged_ids = set()
        self._drop_feedback = None
        self._drop_preview = None
        self._drag_scope = []
        self._scope_exit_left = False
        self._scope_started = False
        self._temporary_unlocks = set()
        self._drop_unlocks = set()
        self._drop_member_targets = None
        self._source_ids = set()
        self._source_unlocks = set()
        self._lock_wait = None
        self._lock_wait_started = 0.0
        self._lock_progress_timer = QTimer(self)
        self._lock_progress_timer.setInterval(33)
        self._lock_progress_timer.timeout.connect(self._refresh_lock_progress)
        self.verticalScrollBar().valueChanged.connect(self.hover_expand.cancel)
        self.horizontalScrollBar().valueChanged.connect(self.hover_expand.cancel)
        self.installEventFilter(self.hover_expand)

    def feedback_rects(self, ids):
        ids = set(ids)
        return [QRectF(0, self.rowViewportPosition(row), self.viewport().width(), self.rowHeight(row))
                for row in range(self.rowCount()) if not self.isRowHidden(row) and self.item(row, 0)
                and self.item(row, 0).data(Qt.UserRole) in ids]

    def _drag_groups(self):
        groups = {('step', cid): set(g['members']) for cid, g in self.step_groups.items()}
        groups.update({('loop', cid): set(m) for cid, m in self.loop_ranges.items()})
        groups.update({('comment', cid): set(m) for cid, m in self.comment_ranges.items()})
        return groups

    def _scope_left(self):
        depth = 0
        if self._drag_scope:
            cid = self._drag_scope[-1][1]
            for row in range(self.rowCount()):
                if self.item(row, 0) and self.item(row, 0).data(Qt.UserRole) == cid:
                    label = self.item(row, 2)
                    depth = int(label.data(INDENT_DEPTH_ROLE) or 0) + 1 if label else len(self._drag_scope)
                    break
        return self.columnViewportPosition(2) + 5 + command_indent_width(self.fontMetrics(), depth)

    def _scope_children(self, groups):
        members = groups.get(self._drag_scope[-1]) if self._drag_scope else None
        candidates = [key for key in groups if key not in self._drag_scope
                      and (members is None or key[1] in members)]
        return [key for key in candidates if not any(key[1] in groups[parent]
                for parent in candidates if parent != key)]

    def _hover_target(self, point):
        groups = self._drag_groups()
        row = self.rowAt(point.y())
        item = self.item(row, 0) if row >= 0 else None
        cid = item.data(Qt.UserRole) if item else None
        if self._drag_scope:
            current = self._drag_scope[-1]
            if current not in groups:
                return ('exit', current)
            if self._scope_exit_left or cid not in groups[current] | {current[1]}:
                return ('exit', current)
        rows = [row] if row >= 0 else []
        if row < 0 or point.y() - self.rowViewportPosition(row) <= 6:
            previous = row - 1 if row >= 0 else self.rowCount() - 1
            while previous >= 0 and self.isRowHidden(previous):
                previous -= 1
            if previous >= 0:
                bottom = self.rowViewportPosition(previous) + self.rowHeight(previous)
                if abs(point.y() - bottom) <= 6:
                    rows.insert(0, previous)
        children = self._scope_children(groups)
        for candidate in rows:
            item = self.item(candidate, 0)
            cid = item.data(Qt.UserRole) if item else None
            for key in children:
                if key[1] not in self._dragged_ids and (cid == key[1] or cid in groups[key]):
                    return key
        return None

    def _track_hover(self, point):
        if self._drag_scope and self._hover_point is not None:
            if point.x() < self._hover_point.x() and point.x() < self._scope_left():
                self._scope_exit_left = True
            elif point.x() > self._hover_point.x():
                self._scope_exit_left = False
        self._hover_point = QPoint(point)
        self._arm_hover(self._hover_target(point))

    def _locked_hover_owner(self, target):
        if target is None:
            return None
        key = target[1] if target[0] == 'exit' else target
        if key[0] == 'step':
            group = self.step_groups.get(key[1])
            if group and (group['locked'] or key[1] in self._temporary_unlocks):
                return key[1]
        return None

    def _arm_hover(self, target):
        if target == self.hover_expand.target:
            return
        self._lock_wait = self._locked_hover_owner(target)
        self._lock_wait_started = monotonic()
        self.hover_expand.timer.setInterval(LOCK_DRAG_DWELL_MS if self._lock_wait is not None else 2000)
        self.hover_expand.track(target)
        if self._lock_wait is not None:
            self._lock_progress_timer.start()
        else:
            self._lock_progress_timer.stop()
        self.viewport().update()

    def lock_progress(self, cid):
        if self._lock_wait != cid or not self.hover_expand.timer.isActive():
            return None
        return min(1.0, max(0.0, (monotonic() - self._lock_wait_started) / (LOCK_DRAG_DWELL_MS / 1000.0)))

    def _refresh_lock_progress(self):
        if not self.hover_expand.timer.isActive():
            self._lock_progress_timer.stop()
            self._lock_wait = None
        self.viewport().update()

    def _unlock_drag_group(self, cid):
        group = self.step_groups.get(cid)
        if group is None:
            return
        self._temporary_unlocks.add(cid)
        if self._source_ids and self._source_ids & group['members']:
            self._source_unlocks.add(cid)
        group['locked'] = False
        self.apply_comment_folds()

    def _expand_hovered(self, target):
        if self._hover_point is None or self._hover_target(self._hover_point) != target or not self.isVisible():
            return
        kind, cid = target
        lock_owner = self._locked_hover_owner(target)
        if lock_owner is not None:
            self._unlock_drag_group(lock_owner)
        self._lock_progress_timer.stop()
        self._lock_wait = None
        self.viewport().update()
        if kind == 'exit':
            self._drag_scope.pop()
            self._scope_exit_left = self._scope_exit_left and self._hover_point.x() < self._scope_left()
            self.hover_expand.cancel()
            self._position_drop_line(self._hover_point)
            following = self._hover_target(self._hover_point)
            if following and following[0] == 'exit':
                self._arm_hover(following)
            return
        members = self._drag_groups().get(target, set())
        if kind == 'step':
            if self.step_groups[cid]['collapsed']:
                self.hoverExpandRequested.emit(cid)
            if self.step_groups.get(cid, {}).get('collapsed', True):
                return
        elif kind == 'loop':
            self.set_loop_collapsed(cid, False)
        else:
            self.set_comment_collapsed(cid, False)
        self._drag_scope.append(target)
        self._scope_exit_left = False
        self._pulse_group({cid} | members, 'hover')
        self._position_drop_line(self._hover_point)

    @visual_only
    def _pulse_group(self, ids, kind='expand'):
        if not self.feedback.allowed(len(ids), preview=kind == 'hover', committed=kind != 'hover'):
            return
        rects = self.feedback_rects(ids)
        if rects:
            bounds = rects[0]
            for rect in rects[1:]:
                bounds = bounds.united(rect)
            self.feedback.play(kind, [bounds], count=len(ids), preview=kind == 'hover', committed=kind != 'hover')

    @visual_only
    def _capture_drop_marker(self):
        if not self.feedback.allowed(preview=True):
            return None
        return (QRectF(self._drop_line.geometry()), self.feedback.epoch, self._drop_line.grab())

    def take_drop_feedback(self):
        marker, self._drop_feedback = self._drop_feedback, None
        return marker

    @visual_only
    def show_edit_feedback(self, kind, ids, marker=None):
        if not self.feedback.allowed(len(ids), committed=True):
            return
        self.feedback.play(kind, self.feedback_rects(ids), count=len(ids), committed=True)
        if marker and marker[1] == self.feedback.epoch:
            self.feedback.play('indicator', snapshots=[(marker[0], marker[2])], count=len(ids), committed=True)

    @visual_only
    def _drag_ghost(self, drag, ids):
        if not animation_policy(self).allows(len(ids), preview=True):
            return
        rects = self.feedback_rects(ids)
        if rects:
            rect = rects[0].intersected(QRectF(self.viewport().rect())).toAlignedRect()
            rect.setWidth(min(420, rect.width()))
            if not rect.isEmpty():
                source = self.viewport().grab(rect)
                ghost = source.copy()
                ghost.fill(Qt.transparent)
                painter = QPainter(ghost)
                try:
                    # Keep insertion arrows and the line visible through the dragged row.
                    painter.setOpacity(0.30)
                    painter.drawPixmap(0, 0, source)
                finally:
                    painter.end()
                drag.setPixmap(ghost)
                drag.setHotSpot(QPoint(min(30, rect.width()//2), rect.height()//2))

    def take_drop_member_targets(self):
        targets, self._drop_member_targets = self._drop_member_targets, None
        return targets

    def take_drop_unlocks(self):
        unlocked, self._drop_unlocks = self._drop_unlocks, set()
        return unlocked

    def _cancel_drag_hover(self):
        self.hover_expand.cancel()
        self._hover_point = None
        self._dragged_ids.clear()
        self._drag_scope.clear()
        self._scope_exit_left = False
        self._scope_started = False
        self._drop_preview = None
        self._source_ids.clear()
        self._source_unlocks.clear()
        self._lock_wait = None
        self._lock_progress_timer.stop()
        for cid in self._temporary_unlocks:
            if cid in self.step_groups:
                self.step_groups[cid]['locked'] = True
        self._temporary_unlocks.clear()
        self.apply_comment_folds()

    def hideEvent(self, event):
        self._cancel_drag_hover()
        super().hideEvent(event)

    def _cancel_fold_click(self, *args):
        self._fold_click_timer.stop()
        self._fold_click_id = None

    def _on_fold_double_click(self, *args):
        self._cancel_fold_click()
        self._ignore_fold_click_until = monotonic() + QApplication.doubleClickInterval() / 1000

    def _queue_fold_click(self, row, column):
        self._cancel_fold_click()
        if monotonic() < self._ignore_fold_click_until:
            return
        item = self.item(row, 0)
        if column != 2 or item is None:
            return
        if QApplication.keyboardModifiers() != Qt.KeyboardModifier.NoModifier:
            return
        command_id = item.data(Qt.ItemDataRole.UserRole)
        if command_id in self.step_groups or command_id in self.loop_ranges or command_id in self.comment_ranges:
            self._fold_click_id = command_id
            # Wait out the double-click window so opening settings never folds.
            self._fold_click_timer.start(QApplication.doubleClickInterval())

    def _toggle_clicked_fold(self):
        command_id = self._fold_click_id
        self._fold_click_id = None
        if command_id in self.step_groups:
            self.stepFoldRequested.emit(command_id)
        elif command_id in self.loop_ranges:
            self.set_loop_collapsed(command_id, command_id not in self.collapsed_loops)
        elif command_id in self.comment_ranges:
            self.set_comment_collapsed(command_id, command_id not in self.collapsed_comments)

    def configure_column_order(self, settings, menu_owner):
        """Keep display ordering separate from logical command columns."""
        self._column_settings=settings
        self._column_menu_owner=weakref.ref(menu_owner)
        header=self.horizontalHeader()
        try:
            order=json.loads(settings.get_setting_value('表格列顺序') or '[0,2,3,1,4,5,6]')
            if isinstance(order,list) and len(order)==self.columnCount() and all(type(i) is int for i in order) and sorted(order)==list(range(self.columnCount())):
                for visual,logical in enumerate(order):
                    header.moveSection(header.visualIndex(logical),visual)
        except (TypeError,ValueError):
            pass
        header.setContextMenuPolicy(Qt.ContextMenuPolicy.CustomContextMenu)
        header.customContextMenuRequested.connect(self._show_column_order_menu)
        header.sectionMoved.connect(self._save_column_order)
        header.setToolTip('右击列标题可左移、右移或恢复默认排序')

    def _save_column_order(self, *_):
        header=self.horizontalHeader()
        order=[header.logicalIndex(i) for i in range(header.count())]
        self._column_settings.set_setting_value('表格列顺序',json.dumps(order))

    def move_column(self, logical, direction):
        header=self.horizontalHeader()
        current=header.visualIndex(logical)
        target=current+direction
        if 0<=current<header.count() and 0<=target<header.count():
            header.moveSection(current,target)

    def restore_default_column_order(self):
        header=self.horizontalHeader()
        with QSignalBlocker(header):
            order = [0, 2, 3, 1, 4, 5, 6] if header.count() == 7 else list(range(header.count()))
            for visual, logical in enumerate(order):
                header.moveSection(header.visualIndex(logical),visual)
        self._save_column_order()

    def _show_column_order_menu(self, point):
        header=self.horizontalHeader()
        logical=header.logicalIndexAt(point)
        if logical<0:return
        visual=header.visualIndex(logical)
        menu=QMenu(self)
        left=menu.addAction('左移')
        right=menu.addAction('右移')
        left.setEnabled(visual>0)
        right.setEnabled(visual<header.count()-1)
        left.triggered.connect(lambda:self.move_column(logical,-1))
        right.triggered.connect(lambda:self.move_column(logical,1))
        menu.addSeparator()
        restore=menu.addAction('恢复默认排序')
        restore.triggered.connect(self.restore_default_column_order)
        style_context_menu=_module_imports.load('style_context_menu')
        style_context_menu(menu,self._column_menu_owner() or self)
        menu.exec(header.mapToGlobal(point))
        menu.deleteLater()

    def paintEvent(self, event):
        super().paintEvent(event)
        self._paint_expanded_borders()
        if not 0 <= self.runtime_row < self.rowCount():
            return
        rect = self.visualRect(self.model().index(self.runtime_row, 0))
        rect.setLeft(0)
        rect.setRight(self.viewport().width() - 1)
        if not rect.intersects(self.viewport().rect()):
            return
        painter = QPainter(self.viewport())
        accent = self.palette().color(QPalette.ColorRole.Highlight)
        tint = QColor(accent)
        tint.setAlpha(32)
        painter.fillRect(rect, tint)
        painter.setPen(QPen(accent, 2))
        painter.drawRect(rect.adjusted(1, 1, -1, -1))
        painter.fillRect(rect.left(), rect.top(), 4, rect.height(), accent)
        painter.end()

    def _expanded_border_rects(self):
        if self.isColumnHidden(2):
            return []
        result = []
        for owner_row, first, last in self._expanded_border_runs:
            label = self.item(owner_row, 2)
            if label is None:
                continue
            depth = label.data(INDENT_DEPTH_ROLE) or 0
            metrics = self.fontMetrics()
            left = self.columnViewportPosition(2) + 5
            left += command_indent_width(metrics, depth)
            left += metrics.horizontalAdvance('▾') // 2
            right = self.columnViewportPosition(2) + self.columnWidth(2) - 1
            top = self.rowViewportPosition(first)
            bottom = self.rowViewportPosition(last) + self.rowHeight(last) - 1
            if left < right:
                result.append((left, top, right, bottom))
        return result

    def _paint_expanded_borders(self):
        painter = QPainter(self.viewport())
        painter.setClipRect(self.columnViewportPosition(2), 0,
                            self.columnWidth(2), self.viewport().height())
        color = QColor('#ffffff' if self.palette().color(QPalette.Base).lightness() < 128 else '#000000')
        painter.setPen(QPen(color, 1))
        for left, top, right, bottom in self._expanded_border_rects():
            painter.drawLine(left, top, left, bottom)
            painter.drawLine(right, top, right, bottom)
            painter.drawLine(left, bottom, right, bottom)
        painter.end()

    def _update_expanded_border_runs(self):
        # Split disjoint ranges so unrelated instructions are never enclosed.
        visible = [(row, self.item(row, 0).data(Qt.UserRole))
                   for row in range(self.rowCount())
                   if self.item(row, 0) is not None and not self.isRowHidden(row)]
        owners = {key: row for row, key in visible}
        groups = [(key, group['members']) for key, group in self.step_groups.items()
                  if not group['collapsed']]
        groups += [(key, members) for key, members in self.loop_ranges.items()
                   if key not in self.collapsed_loops]
        groups += [(key, members) for key, members in self.comment_ranges.items()
                   if key not in self.collapsed_comments]
        self._expanded_border_runs = []
        for key, members in groups:
            if key not in owners:
                continue
            first = last = None
            for row, command_id in visible:
                if row > owners[key] and command_id in members:
                    if first is None:
                        first = row
                    last = row
                elif first is not None:
                    self._expanded_border_runs.append((owners[key], first, last))
                    first = last = None
            if first is not None:
                self._expanded_border_runs.append((owners[key], first, last))
        self.viewport().update()

    def selected_command_ids(self):
        rows = sorted({index.row() for index in self.selectedIndexes()})
        return [int(self.item(row, 0).data(Qt.ItemDataRole.UserRole)) for row in rows if self.item(row, 0) is not None]

    def keyPressEvent(self, event):
        if event.key() in (Qt.Key.Key_Delete, Qt.Key.Key_Backspace):
            self.deleteRequested.emit()
        elif event.matches(QKeySequence.StandardKey.Cut):
            self.cutRequested.emit()
        elif event.matches(QKeySequence.StandardKey.Copy):
            self.copyRequested.emit()
        elif event.matches(QKeySequence.StandardKey.Paste):
            self.pasteRequested.emit()
        else:
            super().keyPressEvent(event)
            return
        event.accept()

    def update_comment_ranges(self, snapshot):
        self._cancel_fold_click()
        from anclicker.domain.step_folding import folding_groups
        self.step_groups = folding_groups(snapshot.commands)
        for cid in self._temporary_unlocks:
            if cid in self.step_groups:
                self.step_groups[cid]['locked'] = False
        connected_fold_ranges = _module_imports.load('connected_fold_ranges')
        self.comment_ranges = connected_fold_ranges(snapshot)
        loop_groups = _module_imports.load('loop_groups')
        self.loop_ranges = loop_groups(snapshot)
        self.collapsed_loops.intersection_update(self.loop_ranges)
        self.collapsed_comments.intersection_update(self.comment_ranges)
        self.apply_comment_folds()

    def set_comment_collapsed(self, command_id, collapsed):
        if command_id not in self.comment_ranges:
            return
        if collapsed:
            self.collapsed_comments.add(command_id)
        else:
            self.collapsed_comments.discard(command_id)
        self.apply_comment_folds()

    def set_loop_collapsed(self, command_id, collapsed):
        if command_id not in self.loop_ranges:
            return
        if collapsed:
            self.collapsed_loops.add(command_id)
        else:
            self.collapsed_loops.discard(command_id)
        self.apply_comment_folds()

    def apply_comment_folds(self):
        from anclicker.domain.step_folding import hidden_steps, group_title
        hidden = hidden_steps(self.step_groups)
        for command_id in self.collapsed_comments:
            hidden.update(self.comment_ranges.get(command_id, ()))
        for command_id in self.collapsed_loops:
            hidden.update(self.loop_ranges.get(command_id, ()))
        for row in range(self.rowCount()):
            item = self.item(row, 0)
            label = self.item(row, 2)
            if item is not None and label is not None:
                command_id = item.data(Qt.ItemDataRole.UserRole)
                label.setData(FOLD_LOCK_ROLE, self.step_groups[command_id]['locked'] if command_id in self.step_groups else None)
                base = label.toolTip()
                depth = sum(command_id in members for members in self.loop_ranges.values())
                depth += sum(command_id in group['members'] for group in self.step_groups.values())
                depth += sum(command_id in members for members in self.comment_ranges.values())
                label.setData(INDENT_DEPTH_ROLE, depth)
                if command_id in self.step_groups:
                    label.setText(group_title(self.step_groups[command_id]))
                elif command_id in self.loop_ranges:
                    arrow = '▸' if command_id in self.collapsed_loops else '▾'
                    label.setText(f'{arrow} {base}（{len(self.loop_ranges[command_id])} 条）')
                elif command_id in self.comment_ranges:
                    arrow = '▸' if command_id in self.collapsed_comments else '▾'
                    label.setText(f'{arrow} {base}（{len(self.comment_ranges[command_id])} 条）')
                elif label.text() != base:
                    label.setText(base)
            self.setRowHidden(row, item is not None and item.data(Qt.ItemDataRole.UserRole) in hidden)

        self._update_expanded_border_runs()

    def _insert_menu_command(self, type_id, before_id):
        if before_id != 'end' and not any(self.item(row, 0) and self.item(row, 0).data(Qt.UserRole) == before_id
                                          for row in range(self.rowCount())):
            return
        targets = {owner for owner, group in self.step_groups.items() if before_id in group['members']}
        locked = {owner for owner in targets if self.step_groups[owner]['locked']}
        if locked and QMessageBox.question(self, '在锁定集合内插入',
                '当前位置处于锁定集合中，是否继续插入？插入完成后会保持加锁。',
                QMessageBox.Yes | QMessageBox.No, QMessageBox.No) != QMessageBox.Yes:
            return
        self._drop_unlocks = locked
        self._drop_member_targets = targets
        try:
            self.instructionDropped.emit(type_id, before_id)
        finally:
            self._drop_unlocks.clear()
            self._drop_member_targets = None

    def contextMenuEvent(self, event):
        index = self.indexAt(event.pos())
        if index.isValid() and (not self.selectionModel().isSelected(index)):
            self.clearSelection()
            self.setCurrentCell(index.row(), index.column())
        menu = MenuColumn(self)
        style_context_menu = _module_imports.load('style_context_menu')
        style_context_menu(menu, self)
        item = self.item(index.row(), 0) if index.isValid() else None
        command_id = item.data(Qt.ItemDataRole.UserRole) if item is not None else None
        run_from = menu.addAction('在此指令运行')
        run_from.setEnabled(command_id is not None)
        menu.addSeparator()
        if command_id in self.step_groups:
            group = self.step_groups[command_id]
            if group.get('kind') == '多线程启动':
                menu.addAction('打开嵌套多线程', lambda: self.threadNestedRequested.emit(command_id, True))
                menu.addAction('取消嵌套多线程', lambda: self.threadNestedRequested.emit(command_id, False))
                menu.addAction('解散线程(保留步骤)', lambda: self.dissolveThreadRequested.emit(command_id))
                menu.addSeparator()
            menu.addAction('展开步骤' if group['collapsed'] else '折叠步骤',
                           lambda: self.stepFoldRequested.emit(command_id))
            menu.addSeparator()
        if command_id in self.loop_ranges:
            collapsed = command_id in self.collapsed_loops
            menu.addAction('展开循环内容' if collapsed else '折叠循环内容',
                           lambda: self.set_loop_collapsed(command_id, not collapsed))
            menu.addSeparator()
        if command_id in self.comment_ranges:
            expand = menu.addAction('展开下部指令', lambda : self.set_comment_collapsed(command_id, False))
            collapse = menu.addAction('收缩下部指令', lambda : self.set_comment_collapsed(command_id, True))
            expand.setEnabled(command_id in self.collapsed_comments)
            collapse.setEnabled(command_id not in self.collapsed_comments and bool(self.comment_ranges[command_id]))
            menu.addSeparator()
        animation_menu(menu, self)
        menu.addSeparator()
        selected_ids = self.selected_command_ids()
        count = len(selected_ids)
        selection_locked = any(group['locked'] and set(selected_ids) & ({owner} | group['members'])
                               for owner, group in self.step_groups.items())
        lock_selection = menu.addAction('解锁' if selection_locked else '折叠加锁',
            lambda: self.stepLocksRequested.emit(selected_ids, not selection_locked))
        lock_selection.setEnabled(count > 0)
        menu.addSeparator()
        copy = menu.addAction(f'复制选中指令（{count} 行）', self.copyRequested.emit)
        copy.setEnabled(count > 0)
        cut = menu.addAction(f'剪切选中指令（{count} 行）', self.cutRequested.emit)
        cut.setEnabled(count > 0)
        above = menu.addAction('粘贴指令到选择上方', lambda: self.pasteRelativeRequested.emit('above'))
        below = menu.addAction('粘贴指令到选择下方', lambda: self.pasteRelativeRequested.emit('below'))
        above.setEnabled(count > 0)
        below.setEnabled(count > 0)
        menu.addAction('粘贴指令到表格末尾', lambda: self.pasteRelativeRequested.emit('end'))
        up = menu.addAction('上移选中指令', lambda: self.moveSelectionRequested.emit(-1))
        down = menu.addAction('下移选中指令', lambda: self.moveSelectionRequested.emit(1))
        rows = {index.row() for index in self.selectedIndexes()}
        up.setEnabled(any(row > 0 and row - 1 not in rows for row in rows))
        down.setEnabled(any(row + 1 < self.rowCount() and row + 1 not in rows for row in rows))
        menu.addSeparator()
        delete = menu.addAction(f'删除选中指令（{count} 行）')
        delete.setEnabled(count > 0)
        insert_menu = MenuColumn(self)
        style_context_menu(insert_menu, self)
        insert_menu.addAction(f'在第 {index.row()+1} 行上方插入指令' if index.isValid() else '在表格末尾插入指令').setEnabled(False)
        action_types = add_instruction_categories(insert_menu, self.instruction_specs_provider(), self)
        before_id = command_id if command_id is not None else 'end'
        try:
            chosen = exec_two_column_menu(menu, insert_menu, event.globalPos(), self)
            if chosen is run_from and command_id is not None:
                self.runFromRequested.emit(command_id)
            elif chosen is delete:
                # Confirmation must open after the popup removes its global
                # event filter, which otherwise consumes clicks on the dialog.
                self.deleteRequested.emit()
            elif chosen in action_types:
                self._insert_menu_command(action_types[chosen], before_id)
        finally:
            menu.deleteLater()
            insert_menu.deleteLater()

    def _lock_at(self, point):
        index = self.indexAt(point)
        if index.isValid() and index.column() == 2 and index.data(FOLD_LOCK_ROLE) is not None:
            if fold_lock_rect(self.visualRect(index)).contains(point):
                return index.data(Qt.ItemDataRole.UserRole)
        return None

    def mouseDoubleClickEvent(self, event):
        if self._lock_at(event.position().toPoint()) is not None:
            self._cancel_fold_click()
            self._lock_press = None
            event.accept()
            return
        super().mouseDoubleClickEvent(event)

    def mousePressEvent(self, event):
        self._row_press = None
        self._lock_press = self._lock_at(event.position().toPoint()) if event.button() == Qt.MouseButton.LeftButton else None
        if self._lock_press is not None:
            self._cancel_fold_click()
            event.accept()
            return
        index = self.indexAt(event.position().toPoint())
        if event.button() == Qt.MouseButton.LeftButton and index.isValid():
            control = bool(event.modifiers() & Qt.ControlModifier)
            selected = self.selected_command_ids()
            command_id = self.item(index.row(), 0).data(Qt.ItemDataRole.UserRole)
            if control and command_id in selected:
                self._cancel_fold_click()
                # Delay Ctrl-click deselection until release, preserving the drag selection.
                self._row_press = (event.position().toPoint(), selected, index.row())
                event.accept()
                return
            if index.column() == 0 and not event.modifiers():
                self.selectRow(index.row())
                self._row_press = (event.position().toPoint(), [command_id], None)
                event.accept()
                return
        super().mousePressEvent(event)

    def mouseMoveEvent(self, event):
        if self._lock_press is not None:
            event.accept()
            return
        if self._row_press is not None and event.buttons() & Qt.MouseButton.LeftButton:
            (origin, command_ids, toggle_row) = self._row_press
            if (event.position().toPoint() - origin).manhattanLength() >= QApplication.startDragDistance():
                self._row_press = None
                drag = QDrag(self)
                mime = QMimeData()
                mime.setData(self.ROW_MIME, json.dumps(command_ids).encode('ascii'))
                drag.setMimeData(mime)
                self._dragged_ids = set(command_ids)
                for owner, group in self.step_groups.items():
                    if group['locked'] and self._dragged_ids & ({owner} | group['members']):
                        self._dragged_ids.update({owner} | group['members'])
                self._drag_ghost(drag, self._dragged_ids)
                try:
                    action = drag.exec(Qt.DropAction.MoveAction)
                finally:
                    self._cancel_drag_hover()
                    self._drop_line.hide()
                if action == Qt.IgnoreAction:
                    self.feedback.play('rebound', self.feedback_rects(command_ids), count=len(command_ids), preview=True)
            return
        super().mouseMoveEvent(event)

    def mouseReleaseEvent(self, event):
        press, self._row_press = self._row_press, None
        if press is not None and press[2] is not None:
            if event.button() == Qt.MouseButton.LeftButton:
                self.selectionModel().select(self.model().index(press[2], 0),
                    QItemSelectionModel.Deselect | QItemSelectionModel.Rows)
            event.accept()
            return
        if self._lock_press is not None:
            command_id, self._lock_press = self._lock_press, None
            if event.button() == Qt.MouseButton.LeftButton and self._lock_at(event.position().toPoint()) == command_id:
                self.stepLockRequested.emit(command_id)
            event.accept()
            return
        super().mouseReleaseEvent(event)

    def _raw_drop_boundary(self, point):
        """Nearest visible row edge; never use the cell column as a drop target."""
        row = self.rowAt(point.y())
        if row >= 0:
            top = self.rowViewportPosition(row)
            bottom = top + self.rowHeight(row)
            if point.y() - top <= bottom - point.y():
                return row, top
            following = row + 1
            while following < self.rowCount() and self.isRowHidden(following):
                following += 1
            return following, bottom
        visible = [r for r in range(self.rowCount()) if not self.isRowHidden(r)]
        if not visible:
            return self.rowCount(), 0
        first, last = visible[0], visible[-1]
        if point.y() < self.rowViewportPosition(first):
            return first, self.rowViewportPosition(first)
        return self.rowCount(), self.rowViewportPosition(last) + self.rowHeight(last)

    def _drop_boundary(self, point):
        from anclicker.domain.step_folding import locked_insertion_boundary
        boundary, y = self._raw_drop_boundary(point)
        ids = [self.item(row, 0).data(Qt.UserRole) if self.item(row, 0) else None
               for row in range(self.rowCount())]
        positions = {cid: row for row, cid in enumerate(ids)}
        groups = self._drag_groups()
        if self._drag_scope:
            key = self._drag_scope[-1]
            rows = [positions[cid] for cid in groups.get(key, set()) | {key[1]} if cid in positions]
            if rows:
                boundary = max(min(rows) + 1, min(boundary, max(rows) + 1))
        # A child collection occupies a single slot until the dwell enters it.
        for key in self._scope_children(groups):
            rows = [positions[cid] for cid in groups[key] | {key[1]} if cid in positions]
            if not rows:
                continue
            start, end = min(rows), max(rows) + 1
            if start < boundary < end:
                visible = [row for row in rows if not self.isRowHidden(row)]
                top = self.rowViewportPosition(start)
                last = max(visible) if visible else start
                bottom = self.rowViewportPosition(last) + self.rowHeight(last)
                boundary = start if point.y() < (top + bottom) / 2 else end
        snapped = locked_insertion_boundary(ids, self.step_groups, boundary)
        # Hidden rows have no useful viewport position: use the preceding visible edge.
        if snapped < self.rowCount() and not self.isRowHidden(snapped):
            y = self.rowViewportPosition(snapped)
        else:
            previous = snapped - 1
            while previous >= 0 and self.isRowHidden(previous):
                previous -= 1
            y = self.rowViewportPosition(previous) + self.rowHeight(previous) if previous >= 0 else 0
        return snapped, y

    def _drop_row(self, event):
        return self._drop_boundary(event.position().toPoint())[0]

    @staticmethod
    def _type_id(event_):
        if not event_.mimeData().hasFormat(INSTRUCTION_MIME_TYPE):
            return None
        try:
            type_id = bytes(event_.mimeData().data(INSTRUCTION_MIME_TYPE)).decode('utf-8')
            from anclicker.instructions.registry import get_instruction_spec
            get_instruction_spec(type_id)
            return type_id
        except (UnicodeDecodeError, KeyError):
            return None

    def _internal_row_drag(self, event):
        return event.source() is self and event.mimeData().hasFormat(self.ROW_MIME)

    def _show_drop_line(self, event):
        point = event.position().toPoint()
        if self._internal_row_drag(event):
            try:
                values = json.loads(bytes(event.mimeData().data(self.ROW_MIME)).decode('ascii'))
                self._source_ids = {values} if type(values) is int else set(values)
                self._dragged_ids = set(self._source_ids)
                previous = None
                while previous != self._dragged_ids:
                    previous = set(self._dragged_ids)
                    for owner, group in self.step_groups.items():
                        if group['locked'] and self._dragged_ids & ({owner} | group['members']):
                            self._dragged_ids.update({owner} | group['members'])
            except (ValueError, TypeError, UnicodeDecodeError):
                self._cancel_drag_hover()
        else:
            self._dragged_ids.clear()
            self._source_ids.clear()
        if not self._scope_started:
            self._scope_started = True
            groups = self._drag_groups()
            parents = [key for key, members in groups.items() if self._source_ids
                       and self._source_ids <= members]
            self._drag_scope = sorted(parents, key=lambda key: len(groups[key]), reverse=True)
        scroll = self.verticalScrollBar()
        if point.y() < 20:
            scroll.setValue(scroll.value() - 1)
        elif point.y() > self.viewport().height() - 20:
            scroll.setValue(scroll.value() + 1)
        self._track_hover(point)
        self._position_drop_line(point)

    def _position_drop_line(self, point):
        boundary, y = self._drop_boundary(point)
        self._drop_preview = (boundary, {key[1] for key in self._drag_scope})
        height = min(14, self.viewport().height())
        left = max(0, min(self._scope_left(), max(0, self.viewport().width() - 24)))
        self._drop_line.setGeometry(left, max(0, min(y - height // 2, self.viewport().height() - height)), self.viewport().width() - left, height)
        self._drop_line.raise_()
        self._drop_line.show()

    def dragEnterEvent(self, event_):
        self._cancel_fold_click()
        if self._internal_row_drag(event_) or self._type_id(event_):
            self._show_drop_line(event_)
            event_.acceptProposedAction()
        else:
            self._cancel_drag_hover()
            self._drop_line.hide()
            event_.ignore()

    def dragMoveEvent(self, event_):
        if self._internal_row_drag(event_) or self._type_id(event_):
            self._show_drop_line(event_)
            event_.acceptProposedAction()
        else:
            self._cancel_drag_hover()
            self._drop_line.hide()
            event_.ignore()

    def dropEvent(self, event_):
        # A member cannot escape its locked source until each enclosing lock has completed.
        if any(group['locked'] and self._source_ids & group['members'] and owner not in self._source_ids
               for owner, group in self.step_groups.items()):
            self._cancel_drag_hover()
            self._drop_line.hide()
            event_.ignore()
            return
        drop_row, targets = self._drop_preview if self._drop_preview is not None else (self._drop_row(event_), {key[1] for key in self._drag_scope})
        self._drop_member_targets = set(targets)
        self._drop_unlocks = (self._temporary_unlocks & targets) | self._source_unlocks
        self._drop_feedback = self._capture_drop_marker()
        self._cancel_drag_hover()
        self._drop_line.hide()
        self._cancel_fold_click()
        if self._internal_row_drag(event_):
            try:
                command_ids = json.loads(bytes(event_.mimeData().data(self.ROW_MIME)).decode('ascii'))
                if isinstance(command_ids, int):
                    command_ids = [command_ids]
                if not isinstance(command_ids, list) or not command_ids or any(type(cid) is not int for cid in command_ids):
                    raise ValueError('无效的拖拽指令')
            except (ValueError, UnicodeDecodeError):
                event_.ignore()
                return
            self.rowsMoved.emit(command_ids, drop_row)
            self._drop_unlocks.clear()
            self._drop_member_targets = None
            event_.acceptProposedAction()
            return
        type_id_ = self._type_id(event_)
        if type_id_:
            row = drop_row
            # Keep a stable ID while the parameter dialog is open, not a row index.
            before_id = self.item(row, 0).data(Qt.ItemDataRole.UserRole) if row < self.rowCount() else 'end'
            event_.acceptProposedAction()
            self.instructionDropped.emit(type_id_, before_id)
            self._drop_unlocks.clear()
            self._drop_member_targets = None
        else:
            # Native item-model drops can overwrite the sequence/name cells.
            event_.ignore()

    def dragLeaveEvent(self, event):
        self._cancel_drag_hover()
        self._drop_line.hide()
        event.accept()

class InstructionTableController:

    def __init__(self, workspace):
        self.workspace = weakref.proxy(workspace)

    def _build_table_view(self) -> None:
        workspace = self.workspace
        workspace.command_table = InstructionTableWidget(0, 7)
        workspace.command_table.instruction_specs_provider = lambda: workspace.window.workspace.editor.view._instruction_specs
        workspace.command_table.setObjectName('commandTable')
        workspace.command_table.viewport().setObjectName('commandTableViewport')
        workspace.command_table.setMouseTracking(True)
        workspace.command_table.setHorizontalHeaderLabels(['序号', '编号', '指令', '参数', '重复', '异常处理', '备注'])
        workspace.command_table.setSelectionBehavior(QAbstractItemView.SelectionBehavior.SelectItems)
        workspace.command_table.setSelectionMode(QAbstractItemView.SelectionMode.ExtendedSelection)
        workspace.command_table.setEditTriggers(QAbstractItemView.EditTrigger.NoEditTriggers)
        workspace.command_table.setAlternatingRowColors(True)
        workspace.command_table.setShowGrid(False)
        workspace.command_table.setWordWrap(False)
        workspace.command_table.verticalHeader().setVisible(False)
        workspace.command_table.verticalHeader().setDefaultSectionSize(38)
        header = workspace.command_table.horizontalHeader()
        header.setSectionResizeMode(QHeaderView.ResizeMode.Interactive)
        header.setStretchLastSection(False)
        header.setMinimumSectionSize(48)
        for (column, width) in enumerate((64, 72, 220, 360, 64, 160, 180)):
            header.resizeSection(column, width)
        workspace.command_table.configure_column_order(workspace.window.db,workspace.window)
        workspace.command_table.setHorizontalScrollBarPolicy(Qt.ScrollBarPolicy.ScrollBarAsNeeded)
        workspace.command_table.cellDoubleClicked.connect(workspace._edit_table_command)
        workspace.command_table.runFromRequested.connect(workspace.window.workspace.run_from_command)
        workspace.command_table.instructionDropped.connect(workspace._add_table_command)
        workspace.command_table.deleteRequested.connect(workspace.delete_table_commands)
        workspace.command_table.copyRequested.connect(workspace.copy_table_commands)
        workspace.command_table.cutRequested.connect(lambda: workspace.window.workspace.cut_commands(workspace.command_table.selected_command_ids()))
        workspace.command_table.dissolveThreadRequested.connect(workspace.window.workspace.dissolve_thread)
        workspace.command_table.pasteRequested.connect(workspace.paste_table_commands)
        workspace.command_table.pasteRelativeRequested.connect(workspace.paste_table_commands)
        workspace.command_table.rowsMoved.connect(workspace.move_table_commands)
        workspace.command_table.moveSelectionRequested.connect(
            lambda direction: self.move_table_commands(workspace.command_table.selected_command_ids(), None, direction=direction))
        workspace.command_table.stepFoldRequested.connect(workspace.window.workspace.toggle_step_fold)
        workspace.command_table.hoverExpandRequested.connect(workspace.window.workspace.expand_step_for_drag)
        workspace.command_table.threadNestedRequested.connect(workspace.window.workspace.set_thread_nested)
        workspace.command_table.stepLockRequested.connect(workspace.window.workspace.toggle_step_lock)
        workspace.command_table.stepLocksRequested.connect(workspace.window.workspace.set_step_locks)
        workspace.command_table.setToolTip('拖拽时悬停折叠行 2 秒逐级展开；右键可设置拖拽动画。从指令栏拖入任意列，最近的行间边界高亮，松开后在高亮处插入；单击指令列中的折叠步骤、循环或注释起点可折叠/展开，双击编辑设置；折叠步骤末尾的开锁/闭锁图标切换整体移动，锁定后拖动组内任意行的序号可整体移动；拖动序号上下排序；其他单元格拖动框选后右键加锁/解锁，Ctrl+C / Ctrl+V 复制粘贴，Delete 删除选中行')
        workspace.window.horizontalLayout.removeWidget(workspace.window.textEdit)
        workspace.window.horizontalLayout.removeItem(workspace.window.verticalLayout)
        for button in (workspace.window.toolButton_8, workspace.window.toolButton_7):
            workspace.window.verticalLayout.removeWidget(button)
        table_panel = QFrame()
        table_panel.setObjectName('workspacePanel')
        table_panel.setProperty('attachedToNavigation', True)
        table_layout = QVBoxLayout(table_panel)
        table_layout.setContentsMargins(6, 4, 6, 4)
        table_layout.setSpacing(2)
        table_title = QLabel('指令表格')
        table_title.setObjectName('sectionTitle')
        table_title.setProperty('compactPanelTitle', True)
        workspace.table_header = QFrame(table_panel)
        title_row = QHBoxLayout(workspace.table_header)
        title_row.setContentsMargins(0, 0, 0, 0)
        title_row.addWidget(table_title)
        title_row.addStretch(1)
        from anclicker.ui.flow_tips import FlowTips
        workspace.table_tips = FlowTips(workspace.window, table_panel, compact=True, default_expanded=False,
            setting='显示表格操作提示', tips=(
                '双击指令可编辑设置；单击指令列中的折叠或循环可收起、展开。',
                '从指令栏拖入表格，高亮的行间位置就是插入位置。',
                '拖动序号可调整指令顺序。',
                '锁定折叠组后，拖动组内序号可整体移动。',
                '选中指令后，Ctrl+C 复制、Ctrl+V 粘贴、Delete 删除。',
                '框选多行后右击，可对折叠组加锁或解锁。',
                '折叠指令末尾的锁图标可切换单行操作与整体操作。',
                '复制锁定的折叠指令时，会同时复制组内指令。',
                '删除锁定的折叠指令时，会连同组内指令一起删除。',
                '删除锁定组内的子指令时，可选择单行删除、整体删除或取消。',
                '收起外层折叠会保留内层折叠状态，再展开时恢复。',
                '鼠标停在提示上会暂停轮播，移开后继续。',
                '点击提示左右箭头可翻页；右击标题栏可收起或展开提示。',
            ))
        workspace.table_tips.setMaximumWidth(680)
        title_row.addWidget(workspace.table_tips, 4)
        title_row.addStretch(1)
        workspace.table_state = QLabel()
        workspace.table_state.setWordWrap(False)
        workspace.table_state.setAlignment(Qt.AlignRight | Qt.AlignVCenter)
        workspace.table_state.setObjectName('mutedText')
        title_row.addWidget(workspace.table_state)
        workspace.table_header.setContextMenuPolicy(Qt.CustomContextMenu)
        workspace.table_header.customContextMenuRequested.connect(
            lambda point: workspace.table_tips.show_toggle_menu(workspace.table_header.mapToGlobal(point)))
        table_layout.addWidget(workspace.table_header)
        table_layout.addWidget(workspace.command_table, 1)
        log_panel = QFrame()
        log_panel.setObjectName('workspacePanel')
        log_layout = QVBoxLayout(log_panel)
        log_layout.setContentsMargins(10, 4, 10, 6)
        log_layout.setSpacing(2)
        log_header = QHBoxLayout()
        log_header.setSpacing(4)
        log_title = QLabel('运行日志')
        log_title.setObjectName('sectionTitle')
        log_title.setProperty('compactPanelTitle', True)
        log_header.addWidget(log_title)
        log_header.addStretch(1)
        workspace.window.toolButton_8.setText('导出日志')
        workspace.window.toolButton_7.setText('清空日志')
        configure_log_actions(workspace.window)
        log_header.addWidget(workspace.window.toolButton_8)
        log_header.addWidget(workspace.window.toolButton_7)
        log_layout.addLayout(log_header)
        log_layout.addWidget(workspace.window.textEdit, 1)
        workspace.table_splitter = QSplitter(Qt.Orientation.Vertical)
        workspace.table_splitter.setObjectName('tableLogSplitter')
        workspace.table_splitter.setChildrenCollapsible(False)
        workspace.command_table.setMinimumHeight(0)
        workspace.command_table.setSizePolicy(QSizePolicy.Policy.Expanding, QSizePolicy.Policy.Ignored)
        workspace.table_splitter.addWidget(table_panel)
        workspace.table_splitter.addWidget(log_panel)
        workspace.table_splitter.setStretchFactor(0, 1)
        workspace.table_splitter.setStretchFactor(1, 1)
        workspace.table_splitter.setHandleWidth(8)
        sizes = [680, 320]
        try:
            saved = json.loads(workspace.window.db.get_setting_value('表格日志面板高度') or 'null')
            if isinstance(saved, list) and len(saved) == 2 and all((isinstance(v, int) and v > 0 for v in saved)):
                sizes = saved
        except (TypeError, ValueError):
            pass
        workspace.table_splitter.setSizes(sizes)
        workspace.table_splitter.splitterMoved.connect(lambda *_: workspace.window.db.set_setting_value('表格日志面板高度', json.dumps(workspace.table_splitter.sizes())))
        workspace.window.horizontalLayout.setContentsMargins(0, 0, 0, 0)
        workspace.window.horizontalLayout.addWidget(workspace.table_splitter, 1)

    def refresh_table(self) -> None:
        workspace = self.workspace
        (snapshot, validation_error) = workspace._current_graph_state()
        commands = list(snapshot.commands)
        workspace.table_state.setText(f'共 {len(commands)} 条指令')
        nodes_by_command = {node.command_id: node for node in snapshot.nodes if node.command_id is not None}
        rows = []
        for (row, command) in enumerate(commands):
            node = nodes_by_command.get(command.id)
            display_name = node.display_name if node is not None else command.type_id
            parameters_text = json.dumps(command.parameters, ensure_ascii=False, sort_keys=True, separators=(', ', ': '))
            if command.type_id == '折叠步骤' and command.note.strip():
                parameters_text = f'备注：{command.note}；{parameters_text}'
            rows.append((command.id, (str(row + 1), f'#{command.id}', display_name, parameters_text, str(command.repeat_count), command.error_policy, command.note)))
        table = workspace.command_table
        refs = [image_references(c.type_id, c.parameters) for c in commands]
        project, folders = '', ()
        if any(refs):
            db = getattr(workspace.window, 'db', None)
            if db is not None:
                project = str(db.get_setting_value('当前文件路径') or '')
                folders = tuple(db.extract_resource_folder_path() or ())
        thumbnails = [(ref, project, folders) if ref else None for ref in refs]
        previous_rows = getattr(workspace, '_table_rows', [])
        if rows == previous_rows:
            for row, key in enumerate(thumbnails):
                item = table.item(row, 2)
                if item is not None and item.data(THUMBNAIL_ROLE) != key:item.setData(THUMBNAIL_ROLE, key)
            table.viewport().update()
            if hasattr(table, 'update_comment_ranges'):
                table.update_comment_ranges(snapshot)
            workspace._apply_comment_row_colors(snapshot)
            return
        order_changed = [r[0] for r in rows] != [r[0] for r in previous_rows]
        selected = [(table.item(index.row(), 0).data(Qt.ItemDataRole.UserRole), index.column()) for index in table.selectedIndexes()]
        current = table.currentItem()
        current_cell = (current.data(Qt.ItemDataRole.UserRole), table.currentColumn()) if current else None
        (scroll_x, scroll_y) = (table.horizontalScrollBar().value(), table.verticalScrollBar().value())
        updates_enabled = table.updatesEnabled()
        table.setUpdatesEnabled(False)
        try:
            with QSignalBlocker(table):
                if order_changed:
                    table.clearSelection()
                table.setRowCount(len(rows))
                for (row, (command_id, values)) in enumerate(rows):
                    if row < len(previous_rows) and rows[row] == previous_rows[row]:
                        table.item(row, 2).setData(THUMBNAIL_ROLE, thumbnails[row])
                        continue
                    for (column, value) in enumerate(values):
                        item = table.item(row, column)
                        if item is None:
                            item = QTableWidgetItem(value)
                            table.setItem(row, column, item)
                        elif item.text() != value:
                            item.setText(value)
                        if item.data(Qt.ItemDataRole.UserRole) != command_id:
                            item.setData(Qt.ItemDataRole.UserRole, command_id)
                        if column == 2:item.setData(THUMBNAIL_ROLE, thumbnails[row])
                        if item.toolTip() != value:
                            item.setToolTip(value)
                if hasattr(table, 'update_comment_ranges'):
                    table.update_comment_ranges(snapshot)
                workspace._apply_comment_row_colors(snapshot)
                workspace._table_rows = rows
                workspace._table_command_rows = {command_id: row for (row, (command_id, _)) in enumerate(rows)}
                if order_changed:
                    if current_cell and current_cell[0] in workspace._table_command_rows:
                        table.setCurrentCell(workspace._table_command_rows[current_cell[0]], current_cell[1], QItemSelectionModel.NoUpdate)
                    else:
                        table.setCurrentCell(-1, -1, QItemSelectionModel.NoUpdate)
                    for (command_id, column) in selected:
                        row = workspace._table_command_rows.get(command_id)
                        if row is not None:
                            table.selectionModel().select(table.model().index(row, column), QItemSelectionModel.Select)
                workspace.highlight_running_command(workspace.running_command_id, ensure_visible=False)
                table.horizontalScrollBar().setValue(scroll_x)
                table.verticalScrollBar().setValue(scroll_y)
        finally:
            table.setUpdatesEnabled(updates_enabled)

    def _apply_comment_row_colors(self, snapshot):
        workspace = self.workspace
        snapshot_disabled_ids = _module_imports.load('snapshot_disabled_ids')
        disabled = snapshot_disabled_ids(snapshot)
        dark = getattr(workspace, 'theme_mode', 'light') == 'dark'
        background = QColor('#3c3c40' if dark else '#dedee3')
        foreground = QColor('#d4d4d8' if dark else '#53535c')
        table = workspace.command_table
        appearance = (dark, tuple((table.item(row, 0).data(Qt.ItemDataRole.UserRole) if table.item(row, 0) else None for row in range(table.rowCount()))), frozenset(disabled))
        if appearance == getattr(workspace, '_table_comment_appearance', None):
            return
        workspace._table_comment_appearance = appearance
        for row in range(table.rowCount()):
            first = table.item(row, 0)
            inactive = first is not None and first.data(Qt.ItemDataRole.UserRole) in disabled
            for column in range(table.columnCount()):
                item = table.item(row, column)
                if item is not None:
                    item.setData(Qt.ItemDataRole.BackgroundRole, background if inactive else None)
                    item.setData(Qt.ItemDataRole.ForegroundRole, foreground if inactive else None)

    def _add_table_command(self, type_id: str, before_command_id='end') -> None:
        workspace = self.workspace
        if not workspace._table_mutation_allowed():
            return
        workspace.window.workspace.add_palette_command(type_id, before_command_id=before_command_id)

    def _edit_table_command(self, row: int, _column: int) -> None:
        workspace = self.workspace
        if _column == 0 or not workspace._table_mutation_allowed():
            return
        item = workspace.command_table.item(row, 0)
        if item is not None:
            workspace.window.workspace.edit_command(item.data(Qt.ItemDataRole.UserRole))
            workspace.refresh_all()

    def _table_mutation_allowed(self):
        workspace = self.workspace
        thread = getattr(workspace.window, 'command_thread', None)
        if thread is not None and thread.isRunning() or workspace.recording_page.busy or workspace.web_recording_page.busy:
            workspace.window.statusBar.showMessage('请先停止运行或录制，再修改表格。', 3000)
            return False
        return True

    def delete_table_commands(self):
        workspace = self.workspace
        if not workspace._table_mutation_allowed():
            return 0
        ids = workspace.command_table.selected_command_ids()
        if not ids:
            return 0
        return workspace.window.workspace.remove_commands(ids)

    def copy_table_commands(self):
        workspace = self.workspace
        asdict = _module_imports.load('asdict')
        ids = set(workspace.command_table.selected_command_ids())
        from anclicker.domain.step_folding import copy_group_drafts, locked_move_ids
        source = workspace.window.workspace.repository.list_commands()
        copied_ids = locked_move_ids(source, ids)
        commands = copy_group_drafts(source, ids, workspace.window.workspace.repository.snapshot())
        if not commands:
            return
        mime = QMimeData()
        payload = json.dumps([asdict(c) for c in commands], ensure_ascii=False)
        mime.setData('application/x-anclicker-commands', payload.encode('utf-8'))
        mime.setText('\n'.join((f'{c.type_id}\t{json.dumps(c.parameters, ensure_ascii=False)}\t{c.repeat_count}\t{c.note}' for c in commands)))
        set_command_mime(mime)
        workspace.window.statusBar.showMessage(f'已复制{command_row_label(source, copied_ids)}，共 {len(commands)} 条指令', 4000)

    def paste_table_commands(self, placement="auto"):
        workspace = self.workspace
        if not workspace._table_mutation_allowed():
            return
        raw = command_clipboard_data()
        if raw is None:
            workspace.window.statusBar.showMessage('请先在指令表格中复制指令。', 2500)
            return
        try:
            InstructionDraft = _module_imports.load('InstructionDraft')
            if len(raw) > 10000000:
                raise ValueError('复制内容过大，请分批粘贴')
            data = json.loads(raw)
            if not isinstance(data, list) or not 0 < len(data) <= 10000 or (not all((isinstance(x, dict) for x in data))):
                raise ValueError('剪贴板不是有效的指令列表')
            drafts = [InstructionDraft.from_mapping(item) for item in data]
            repo = workspace.window.workspace.repository
            if placement == 'auto':
                placement = 'below' if workspace.command_table.selected_command_ids() else 'end'
            if placement == 'end':
                ids = repo.append_recording(drafts, connect=False)
            elif placement in ('above', 'below'):
                table = workspace.command_table
                rows = sorted({index.row() for index in table.selectedIndexes()})
                if not rows:
                    workspace.window.statusBar.showMessage('请先选择插入位置的指令。', 2500)
                    return
                boundary = rows[0] if placement == 'above' else rows[-1] + 1
                before_id = table.item(boundary, 0).data(Qt.ItemDataRole.UserRole) if boundary < table.rowCount() else 'end'
                ids = repo.insert_table_commands(drafts, before_command_id=before_id, placement=placement)
            else:
                raise ValueError('未知的粘贴位置')
            workspace.window.workspace.reload_graph(ids[0])
            workspace.window.workspace.graphFinalized.emit(False)
            feedback_call(workspace.window.workspace, 'expand_drop_targets', ids)
            workspace._select_table_ids(ids)
            feedback_call(workspace.window.workspace, 'edit_feedback', 'copy', ids)
            workspace.window.statusBar.showMessage(f'已粘贴到{command_row_label(repo.list_commands(), ids)}，共 {len(ids)} 条指令', 4000)
        except Exception as error:
            QMessageBox.warning(workspace.window, '粘贴失败', str(error))

    def _select_table_ids(self, ids):
        workspace = self.workspace
        QTableWidgetSelectionRange = _module_imports.load('QTableWidgetSelectionRange')
        table = workspace.command_table
        table.clearSelection()
        first_row = next((row for row in range(table.rowCount())
                          if table.item(row, 0).data(Qt.ItemDataRole.UserRole) in ids), None)
        if first_row is not None:
            table.setCurrentCell(first_row, 0, QItemSelectionModel.NoUpdate)
            table.scrollToItem(table.item(first_row, 0))
        for row in range(workspace.command_table.rowCount()):
            if workspace.command_table.item(row, 0).data(Qt.ItemDataRole.UserRole) in ids:
                workspace.command_table.setRangeSelected(QTableWidgetSelectionRange(row, 0, row, workspace.command_table.columnCount() - 1), True)

    def move_table_commands(self, ids, destination, *, direction=None):
        workspace = self.workspace
        marker = feedback_call(getattr(workspace, 'command_table', None), 'take_drop_feedback')
        unlocked = feedback_call(getattr(workspace, 'command_table', None), 'take_drop_unlocks') or set()
        member_targets = feedback_call(getattr(workspace, 'command_table', None), 'take_drop_member_targets')
        if not workspace._table_mutation_allowed():
            return
        repo = workspace.window.workspace.repository
        from anclicker.domain.step_folding import locked_move_ids, folding_groups, locked_insertion_boundary
        commands = repo.list_commands()
        for command in commands:
            if command.id in unlocked:
                command.parameters['整体锁定'] = False
        current = [c.id for c in commands]
        from anclicker.domain.flow_loop_table import loop_groups
        loops = loop_groups(repo.snapshot())
        ids = set(ids)
        while True:
            previous = set(ids)
            ids = locked_move_ids(commands, ids)
            for header, members in loops.items():
                if header in ids:
                    ids.update(members)
            if ids == previous:
                break
        moved = [item for item in current if item in ids]
        if not moved:
            return
        if direction is not None:
            from anclicker.domain.table_movement import move_selected_one_step
            ordered = move_selected_one_step(current, ids, folding_groups(commands), direction)
        else:
            remaining = [item for item in current if item not in ids]
            destination = locked_insertion_boundary(current, folding_groups(commands), destination)
            index = destination - sum((item in ids for item in current[:destination]))
            ordered = remaining[:index] + moved + remaining[index:]
        if ordered == current and member_targets is None:
            return
        try:
            rewired = repo.reorder_table_commands(ordered, temporary_unlocks=unlocked, inserted_members=moved, member_targets=member_targets) if unlocked or member_targets is not None else repo.reorder_table_commands(ordered)
            workspace.window.workspace.reload_graph(moved[0])
            workspace.window.workspace.graphFinalized.emit(False)
            feedback_call(workspace.window.workspace, 'expand_drop_targets', moved)
            workspace._select_table_ids(moved)
            feedback_call(workspace.window.workspace, 'edit_feedback', 'move', moved, marker)
            workspace.window.statusBar.showMessage('已同步表格排序和流程图' + ('；顺序连线已调整' if rewired else '；分支或循环连线保持不变'), 4000)
        except Exception as error:
            QMessageBox.warning(workspace.window, '移动失败', str(error))
