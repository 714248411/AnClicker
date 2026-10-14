"""Control-flow direction markers, spaced and animated in viewport pixels."""
import math
from collections import defaultdict
from qt_compat.QtCore import QPointF, QRectF
from qt_compat.QtGui import QPainterPath, QRegion

ARROW_SPACING = 36.0
ARROW_SPEED = 36.0
ARROW_LENGTH = 8.0
ARROW_HALF_WIDTH = 4.0


def control_edges(edges, depth=2):
    """Error links and the two incoming/outgoing steps of loops and conditions.

    Walk each direction separately: an unrelated sibling branch must not become
    animated just because it shares a predecessor with a condition.
    """
    incoming, outgoing = defaultdict(list), defaultdict(list)
    controls = set()
    for edge in edges:
        if edge.link_kind in (5, 6):
            continue
        incoming[edge.target_node].append(edge)
        outgoing[edge.source_node].append(edge)
        controls.update(node for node in (edge.source_node, edge.target_node)
                        if node.control_kind in ('loop', 'condition'))
    # Error links have their own markers without expanding into ordinary paths.
    selected = {edge for edge in edges if edge.link_kind in (5, 6)}
    for adjacency, attribute in ((incoming, 'source_node'), (outgoing, 'target_node')):
        frontier, visited = controls, set(controls)
        for _ in range(depth):
            next_nodes = set()
            for node in frontier:
                for edge in adjacency[node]:
                    selected.add(edge)
                    neighbor = getattr(edge, attribute)
                    if neighbor not in visited:
                        next_nodes.add(neighbor)
            visited.update(next_nodes)
            frontier = next_nodes
    return tuple(edge for edge in edges if edge in selected)


def visible_segment(a, b, rect):
    """Clipped parametric interval; avoids sampling miles of offscreen line."""
    dx, dy = b.x()-a.x(), b.y()-a.y()
    low, high = 0.0, 1.0
    for direction, distance in ((-dx, a.x()-rect.left()), (dx, rect.right()-a.x()),
                                (-dy, a.y()-rect.top()), (dy, rect.bottom()-a.y())):
        if abs(direction) < 1e-12:
            if distance < 0:
                return None
        elif direction < 0:
            low = max(low, distance/direction)
        else:
            high = min(high, distance/direction)
        if low > high:
            return None
    return low, high


def arrow_segments(path, transform):
    segments, distance = [], 0.0
    for polygon in path.toSubpathPolygons(transform):
        for a, b in zip(polygon, list(polygon)[1:]):
            length = math.hypot(b.x()-a.x(), b.y()-a.y())
            if length > 1e-8:
                segments.append((a, b, distance, length))
                distance += length
    return segments, distance


def moving_arrows(segments, total, viewport, elapsed):
    """Return screen-space chevrons; zoom never changes spacing, size or speed."""
    result = QPainterPath()
    phase = (elapsed * ARROW_SPEED) % ARROW_SPACING
    clip = viewport.adjusted(-ARROW_LENGTH, -ARROW_LENGTH, ARROW_LENGTH, ARROW_LENGTH)
    for a, b, start, length in segments:
        interval = visible_segment(a, b, clip)
        if interval is None:
            continue
        low = max(start+length*interval[0], 14.0)
        high = min(start+length*interval[1], total-14.0)
        distance = phase + math.ceil((low-phase)/ARROW_SPACING)*ARROW_SPACING
        dx, dy = (b.x()-a.x())/length, (b.y()-a.y())/length
        while distance <= high and distance < start+length:
            tip = a + QPointF(dx, dy)*(distance-start)
            tail = tip - QPointF(dx, dy)*ARROW_LENGTH
            side = QPointF(-dy, dx)*ARROW_HALF_WIDTH
            result.moveTo(tail+side)
            result.lineTo(tip)
            result.lineTo(tail-side)
            distance += ARROW_SPACING
    return result


def arrow_repaint_region(segments, viewport):
    """Repaint only visible line corridors, not the entire graph every frame."""
    region = QRegion()
    clip = viewport.adjusted(-12, -12, 12, 12)
    for a, b, _, _ in segments:
        interval = visible_segment(a, b, clip)
        if interval is None:
            continue
        delta = b-a
        bounds = QRectF(a+delta*interval[0], a+delta*interval[1]).normalized()
        bounds = bounds.adjusted(-12, -12, 12, 12).intersected(viewport)
        region |= QRegion(bounds.toAlignedRect())
    return region
