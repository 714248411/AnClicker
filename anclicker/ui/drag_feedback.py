"""Non-blocking, disposable viewport feedback. Never owns a business operation."""
from functools import wraps
from time import monotonic
import json

from anclicker.platform.qt_compat.QtCore import QObject, QEvent, QPoint, QPointF, QRectF, QTimer, Qt, Signal
from anclicker.app.state import application_state
from anclicker.ui.context_menu_style import style_context_menu
from anclicker.platform.qt_compat.QtGui import QColor, QPainter, QPen
from anclicker.platform.qt_compat.QtWidgets import QApplication, QWidget, QInputDialog


def visual_only(function):
    """A failed visual must never make an already committed edit appear to fail."""
    @wraps(function)
    def guarded(*args, **kwargs):
        try:
            return function(*args, **kwargs)
        except Exception:
            return None
    return guarded


@visual_only
def feedback_call(host, method, *args):
    callback = getattr(host, method, None)
    return callback(*args) if callback is not None else None


class AnimationPolicy(QObject):
    changed = Signal()
    SETTING = '拖拽动画设置'

    def __init__(self, owner):
        super().__init__(owner)
        self.enabled = True
        self.batch_limit = 80
        self.skip_offscreen = True
        self.headless = QApplication.platformName().lower() in ('offscreen', 'minimal')
        self.background_batch = False
        self.forced_low_quality = False
        self.blocking_operation = False
        self.degraded_until = 0.0
        self.settings = getattr(owner, 'db', None)
        try:
            values = json.loads(self.settings.get_setting_value(self.SETTING) or '{}') if self.settings else {}
            self.enabled = bool(values.get('enabled', True))
            self.batch_limit = max(1, min(1000, int(values.get('batch_limit', 80))))
            self.skip_offscreen = bool(values.get('skip_offscreen', True))
        except (TypeError, ValueError):
            pass

    def allows(self, count=1, *, committed=False, preview=False):
        owner = self.parent()
        return bool(self.enabled and (committed or preview) and count <= self.batch_limit
                    and not (self.headless or self.background_batch or self.forced_low_quality
                             or self.blocking_operation or getattr(owner, '_closing', False))
                    and monotonic() >= self.degraded_until
                    and not application_state(owner).is_busy()
                    and QApplication.activeModalWidget() is None)

    @visual_only
    def configure(self, **values):
        for key in ('enabled', 'batch_limit', 'skip_offscreen'):
            if key in values:
                setattr(self, key, values[key])
        self.changed.emit()  # Stop active effects before writing preferences.
        if self.settings:
            self.settings.set_setting_value(self.SETTING, json.dumps({
                'enabled': self.enabled, 'batch_limit': self.batch_limit,
                'skip_offscreen': self.skip_offscreen}))


def animation_policy(widget):
    owner = widget.window()
    ancestor = widget
    while ancestor is not None:
        if getattr(ancestor, 'db', None) is not None:
            owner = ancestor
            break
        ancestor = ancestor.parentWidget()
    policy = getattr(owner, '_drag_animation_policy', None)
    if policy is None:
        policy = AnimationPolicy(owner)
        owner._drag_animation_policy = policy
    return policy


@visual_only
def animation_menu(menu, widget):
    policy = animation_policy(widget)
    sub = menu.addMenu('拖拽动画')
    style_context_menu(sub, widget)
    menu._drag_animation_menu = sub  # Keep the PySide2 submenu wrapper alive.
    enabled = sub.addAction('启用拖拽动画(全局)')
    enabled.setCheckable(True)
    enabled.setChecked(policy.enabled)
    enabled.toggled.connect(lambda value: policy.configure(enabled=value))
    skip = sub.addAction('跳过视口外动画')
    skip.setCheckable(True)
    skip.setChecked(policy.skip_offscreen)
    skip.toggled.connect(lambda value: policy.configure(skip_offscreen=value))
    limit = sub.addAction(f'批量动画上限：{policy.batch_limit} 个…')
    def choose_limit():
        value, ok = QInputDialog.getInt(widget, '批量动画上限', '超过此节点数量直接刷新：', policy.batch_limit, 1, 1000)
        if ok:
            policy.configure(batch_limit=value)
    limit.triggered.connect(choose_limit)


class HoverExpandController(QObject):
    """One 2s dwell per visible header; expansion is independent of animations."""
    def __init__(self, owner, expand):
        super().__init__(owner)
        self.expand = expand
        self.target = None
        self.timer = QTimer(self)
        self.timer.setSingleShot(True)
        self.timer.setInterval(2000)
        self.timer.setTimerType(Qt.PreciseTimer)
        self.timer.timeout.connect(self._timeout)

    def track(self, target):
        if target == self.target:
            return
        self.cancel()
        self.target = target
        if target is not None:
            self.timer.start()

    def cancel(self):
        self.timer.stop()
        self.target = None

    def eventFilter(self, watched, event):
        if event.type() in (QEvent.Hide, QEvent.Close, QEvent.KeyPress):
            self.cancel()
        return False

    def _timeout(self):
        target = self.target
        # Keep the consumed key until the pointer enters another header.
        if target is not None:
            try:
                self.expand(target)
            except Exception:
                pass


class FeedbackOverlay(QWidget):
    """Snapshots and outlines only: no item positions, opacity or model writes."""
    def __init__(self, view, *, reduced_motion=False):
        super().__init__(view.viewport())
        self.reduced_motion = reduced_motion
        self.view = view
        self.effects = []
        self.epoch = 0
        self._policy = None
        self._last_tick = 0.0
        self._slow_frames = 0
        self.setAttribute(Qt.WA_TransparentForMouseEvents)
        self.setAttribute(Qt.WA_NoSystemBackground)
        self.setFocusPolicy(Qt.NoFocus)
        self.hide()
        self.timer = QTimer(self)
        self.timer.setInterval(16)
        self.timer.timeout.connect(self._advance)
        view.viewport().installEventFilter(self)
        view.installEventFilter(self)
        view.horizontalScrollBar().valueChanged.connect(self.cancel)
        view.verticalScrollBar().valueChanged.connect(self.cancel)

    @visual_only
    def cancel(self, *_):
        self.timer.stop()
        self.epoch += 1
        self.effects.clear()
        self.hide()

    def eventFilter(self, watched, event):
        if event.type() in (QEvent.Wheel, QEvent.Hide, QEvent.Close, QEvent.Resize,
                            QEvent.MouseButtonPress, QEvent.KeyPress):
            self.cancel()
        return False

    @visual_only
    def allowed(self, count=1, *, committed=False, preview=False):
        return self.view.isVisible() and animation_policy(self.view).allows(count, committed=committed, preview=preview)

    @visual_only
    def capture(self, rects, count=1):
        policy = animation_policy(self.view)
        if not policy.allows(count, preview=True) or not self.view.isVisible():
            return []
        viewport = self.view.viewport()
        result = []
        for rect in rects:
            clipped = QRectF(rect).intersected(QRectF(viewport.rect())).toAlignedRect()
            if not clipped.isEmpty():
                result.append((QRectF(clipped), viewport.grab(clipped)))
        return result

    @visual_only
    def play(self, kind, rects=(), *, count=1, committed=False, preview=False, snapshots=()):
        policy = animation_policy(self.view)
        if self._policy is not policy:
            if self._policy is not None:
                self._policy.changed.disconnect(self.cancel)
            self._policy = policy
            policy.changed.connect(self.cancel)
        if not policy.allows(count, committed=committed, preview=preview) or not self.view.isVisible():
            return False
        visible = QRectF(self.view.viewport().rect())
        entries = [(QRectF(rect), None) for rect in rects] + list(snapshots or ())
        if policy.skip_offscreen:
            entries = [(r, p) for r, p in entries if visible.intersects(r)]
        if not entries:
            return False
        self.setGeometry(self.view.viewport().rect())
        # Bound the work even during repeated edits. Older feedback is disposable.
        self.effects = [] if self.reduced_motion else self.effects[-3:]
        duration = .52 if kind in ('hover', 'expand') else .28 if kind in ('indicator', 'rebound') else .36
        if self.reduced_motion:
            duration = .28
        self.effects.append(dict(kind=kind, entries=entries, start=monotonic(), duration=duration, count=count))
        self._last_tick = monotonic()
        self._slow_frames = 0
        self.show()
        self.raise_()
        self.timer.start()
        self.update()
        return True

    def _advance(self):
        try:
            now = monotonic()
            policy = self._policy
            if not policy or not policy.allows(max((e['count'] for e in self.effects), default=1), preview=True):
                self.cancel()
                return
            self._slow_frames = self._slow_frames + 1 if now - self._last_tick > .08 else 0
            self._last_tick = now
            if self._slow_frames >= 3:
                policy.degraded_until = now + 1.5
                self.cancel()
                return
            self.effects = [e for e in self.effects if now - e['start'] < e['duration']]
            if not self.effects:
                self.cancel()
            else:
                self.update()
        except Exception:
            self.cancel()

    def paintEvent(self, event):
        painter = None
        try:
            painter = QPainter(self)
            painter.setRenderHint(QPainter.Antialiasing)
            painter.setClipRect(self.rect())
            now = monotonic()
            colors = {'move': '#6376e8', 'copy': '#2bb99b', 'link': '#b07be8',
                      'create': '#e7a543', 'delete': '#ee6475', 'rebound': '#ee6475'}
            for effect in self.effects:
                t = max(0., min(1., (now-effect['start']) / effect['duration']))
                ease = 1 - (1-t)**3
                kind = effect['kind']
                for original, pixmap in effect['entries']:
                    rect = QRectF(original).intersected(QRectF(self.rect()))
                    if self.reduced_motion:
                        pass  # Graph feedback stays anchored; never slide or zoom the outline.
                    elif kind == 'delete': rect.translate(-40*ease, 0)
                    elif kind == 'move': rect.translate(0, -12*(1-ease))
                    elif kind == 'copy': rect.translate(14*(1-ease), -8*(1-ease))
                    elif kind == 'rebound': rect.translate(24*(1-ease), 0)
                    elif kind == 'create':
                        rect.adjust(-9*(1-ease), -7*(1-ease), 9*(1-ease), 7*(1-ease))
                    color = QColor(colors.get(kind, '#6376e8'))
                    painter.save()
                    painter.setOpacity((1-t)*(.35 if self.reduced_motion else .75 if pixmap else 1.))
                    if pixmap is not None:
                        painter.drawPixmap(rect.toAlignedRect(), pixmap)
                    elif kind == 'indicator':
                        painter.setPen(QPen(color, 3))
                        painter.drawLine(QPointF(rect.left(), rect.center().y()), QPointF(rect.right(), rect.center().y()))
                    else:
                        tint = QColor(color)
                        tint.setAlpha(0 if self.reduced_motion else 28 if kind in ('hover', 'expand') else 45)
                        painter.setBrush(tint)
                        painter.setPen(QPen(color, 1.5 if self.reduced_motion else 2))
                        if kind == 'link' and not self.reduced_motion:
                            margin = 12*ease
                            rect.adjust(-margin, -margin, margin, margin)
                        painter.drawRoundedRect(rect.adjusted(1, 1, -1, -1), 5, 5)
                    painter.restore()
        except Exception:
            self.cancel()
        finally:
            if painter is not None:
                painter.end()
