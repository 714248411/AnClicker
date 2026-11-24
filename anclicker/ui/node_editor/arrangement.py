"""Explicit canvas arrangement and append-only placement of new instructions."""
from anclicker.platform.qt_compat.QtCore import QRectF, QSettings
from anclicker.platform.qt_compat.QtGui import QFontMetricsF

MODES = ('横向排布', '竖向排布', '横向紧密排布', '竖向紧密排布', '贪吃蛇排布', '竖向贪吃蛇排布')


def next_position(mode, last, width, height, bounds, gap=0):
    x, y = last
    if mode == MODES[0]:
        return x + width, y
    if mode == MODES[1]:
        return x, y + height
    if mode == MODES[3]:
        return (x, y + height) if y + 2 * height - gap <= bounds.bottom() else (x + width, bounds.top())
    if mode == MODES[5]:
        column = max(0, round((x - bounds.left()) / width))
        direction = -1 if column % 2 else 1
        ny = y + direction * height
        if ny < bounds.top() or ny + height - gap > bounds.bottom():
            return x + width, y
        return x, ny
    if mode == MODES[4]:
        row = max(0, round((y - bounds.top()) / height))
        direction = -1 if row % 2 else 1
        nx = x + direction * width
        if nx < bounds.left() or nx + width - gap > bounds.right():
            return x, y + height
        return nx, y
    return (x + width, y) if x + 2 * width - gap <= bounds.right() else (bounds.left(), y + height)


class CanvasArrangement:
    def __init__(self, workspace):
        self.workspace = workspace
        self.settings = QSettings('AnClicker', 'CanvasArrangement')
        self.mode = str(self.settings.value('mode', MODES[2]))
        if self.mode not in MODES:
            self.mode = MODES[2]
        self.bounds = None

    def select(self, mode):
        if mode not in MODES:
            return
        self.mode = mode
        self.bounds = None
        self.settings.setValue('mode', mode)
        self.workspace.statusMessage.emit('已选择' + mode + '，拖入指令保留放置位置；点击刷新整体重新排布可重排全部。')

    def add_menu(self, menu):
        for mode in MODES:
            action = menu.addAction('横向贪吃蛇排布' if mode == MODES[4] else mode)
            action.setCheckable(True)
            action.setChecked(mode == self.mode)
            action.triggered.connect(lambda checked=False, value=mode: self.select(value))
        menu.addSeparator()
        menu.addAction('刷新整体重新排布', self.rearrange)

    def units(self, snapshot):
        scene = self.workspace.editor.scene
        used = set()
        units = []
        for command in snapshot.commands:
            node = scene.nodes_by_command_id.get(command.id)
            if node is None or node.node_id in used:
                continue
            members = scene.locked_groups.get(node.node_id, (node.node_id,))
            used.update(members)
            items = [scene.nodes_by_id[key] for key in members]
            rect = self.card_rect(node)
            for item in items:
                rect = rect.united(self.card_rect(item))
            units.append((node, items, rect))
        return units

    @staticmethod
    def card_rect(node):
        return QRectF(node.x(), node.y(), node.width, node.height + (18.0 if node.note else 0.0))

    def spacing(self):
        nodes = self.workspace.editor.scene.nodes_by_command_id.values()
        font = next((node.title_font for node in nodes), self.workspace.editor.view.font())
        return QFontMetricsF(font).horizontalAdvance('字字字')

    def _bounds(self):
        view = self.workspace.editor.view
        gap = self.spacing()
        rect = view.mapToScene(view.viewport().rect()).boundingRect().adjusted(gap, gap, -gap, -gap)
        return rect

    def positions(self, snapshot, new_ids=None, viewport_bounds=None):
        units = self.units(snapshot)
        if not units:
            return {}
        if new_ids is None:
            scene = self.workspace.editor.scene
            for key, first in (('start', True), ('end', False)):
                node = scene.nodes_by_id.get(key)
                if node is not None:
                    unit = (node, [node], self.card_rect(node))
                    units.insert(0, unit) if first else units.append(unit)
        gap = self.spacing()
        chosen = [u for u in units if new_ids is None or u[0].command_id in new_ids]
        if not chosen:
            return {}
        old = [u for u in units if new_ids is not None and u[0].command_id not in new_ids]
        bounds = QRectF(viewport_bounds) if viewport_bounds is not None else self._bounds()
        self.bounds = QRectF(bounds)
        vertical = self.mode in (MODES[1], MODES[3], MODES[5])
        snake = self.mode in (MODES[4], MODES[5])
        wrap = self.mode not in MODES[:2]
        previous = QRectF(old[-1][2]) if old else None
        direction = 1
        lane = QRectF(previous) if previous is not None else None
        if old:
            aligned = [r for _, _, r in old if abs((r.left()-previous.left()) if vertical else (r.top()-previous.top())) < 0.1]
            for r in aligned:
                lane = lane.united(r)
            if snake and len(aligned) > 1:
                delta = (aligned[-1].top()-aligned[-2].top()) if vertical else (aligned[-1].left()-aligned[-2].left())
                direction = -1 if delta < 0 else 1
            elif snake:
                direction = getattr(self, '_last_direction', 1)
        source = {n.node_id: (n.x, n.y) for n in snapshot.nodes}
        occupied = [rect for _, _, rect in old]
        result = {}

        def advance(w, h):
            nonlocal lane, direction
            if previous is None:
                return QRectF(bounds.left(), bounds.top(), w, h)
            if vertical:
                y = previous.bottom()+gap if direction > 0 else previous.top()-gap-h
                x = previous.left()
                if wrap and ((direction > 0 and y+h > bounds.bottom()) or (direction < 0 and y < bounds.top())):
                    x = lane.right()+gap
                    direction = -direction if snake else 1
                    y = bounds.top() if direction > 0 else bounds.bottom()-h
                    lane = None
            else:
                x = previous.right()+gap if direction > 0 else previous.left()-gap-w
                y = previous.top()
                if wrap and ((direction > 0 and x+w > bounds.right()) or (direction < 0 and x < bounds.left())):
                    y = lane.bottom()+gap
                    direction = -direction if snake else 1
                    x = bounds.left() if direction > 0 else bounds.right()-w
                    lane = None
            return QRectF(x, y, w, h)

        for node, members, rect in chosen:
            candidate = advance(rect.width(), rect.height())
            while any(candidate.intersects(r.adjusted(-gap/2, -gap/2, gap/2, gap/2)) for r in occupied):
                previous = candidate
                lane = candidate if lane is None else lane.united(candidate)
                candidate = advance(rect.width(), rect.height())
            dx, dy = candidate.left()-rect.left(), candidate.top()-rect.top()
            for member in members:
                x, y = source[member.node_id]
                result[member.node_id] = (x+dx, y+dy)
            previous = candidate
            lane = QRectF(candidate) if lane is None else lane.united(candidate)
            occupied.append(QRectF(candidate))
        self._last_direction = direction
        scene = self.workspace.editor.scene
        if new_ids is not None and 'end' in scene.nodes_by_id:
            end = self.card_rect(scene.nodes_by_id['end'])
            target = advance(end.width(), end.height())
            result['end'] = (target.x(), target.y())
        return result

    def place_new(self, snapshot, existing_ids, viewport_bounds=None):
        ids = {c.id for c in snapshot.commands} - existing_ids
        if ids:
            positions = self.positions(snapshot, ids, viewport_bounds)
            if positions:
                self.workspace.repository.save_node_positions(positions)
                return self.workspace.repository.snapshot()
        return snapshot

    def rearrange(self):
        workspace = self.workspace
        try:
            workspace._check_parameter_save_allowed()
            self.bounds = None
            snapshot = workspace.repository.snapshot()
            positions = self.positions(snapshot)
            if positions:
                workspace.repository.save_node_positions(positions)
                workspace.reload_graph()
                workspace.statusMessage.emit('已按' + self.mode + '重新排布全部指令，连线保持不变。')
        except Exception as error:
            workspace._show_error('重新排布失败', error)
