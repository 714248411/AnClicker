"""Bounded spatial lookup for routing a bulk-imported recording before paint."""
import math


class RoutingIndex:
    CELL = 320.0

    def __init__(self):
        self.buckets = {}
        self.wide = set()
        self.records = {}

    def cells(self, rect):
        left, right = math.floor(rect.left() / self.CELL), math.floor(rect.right() / self.CELL)
        top, bottom = math.floor(rect.top() / self.CELL), math.floor(rect.bottom() / self.CELL)
        if (right - left + 1) * (bottom - top + 1) > 4096:
            return None
        return [(x, y) for x in range(left, right + 1) for y in range(top, bottom + 1)]

    def add(self, item, rect, stroke=None):
        old = self.records.get(item)
        if old:
            if old[2] is None:
                self.wide.discard(item)
            else:
                for cell in old[2]:
                    self.buckets[cell].discard(item)
        cells = self.cells(rect)
        self.records[item] = (rect, stroke, cells)
        if cells is None:
            self.wide.add(item)
        else:
            for cell in cells:
                self.buckets.setdefault(cell, set()).add(item)

    def items(self, rect):
        cells = self.cells(rect)
        candidates = set(self.wide)
        if cells is None:
            candidates.update(self.records)
        else:
            for cell in cells:
                candidates.update(self.buckets.get(cell, ()))
        return [item for item in candidates if self.records[item][0].intersects(rect)]
