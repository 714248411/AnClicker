import unittest
from PySide6.QtCore import QRectF
from node_editor.routing_index import RoutingIndex


class RoutingIndexTests(unittest.TestCase):
    def test_query_and_update_do_not_return_stale_edges(self):
        index = RoutingIndex()
        a, b = object(), object()
        index.add(a, QRectF(0, 0, 10, 10))
        index.add(b, QRectF(1000, 1000, 10, 10))
        self.assertEqual(index.items(QRectF(-1, -1, 20, 20)), [a])
        index.add(a, QRectF(2000, 2000, 10, 10))
        self.assertEqual(index.items(QRectF(-1, -1, 20, 20)), [])

    def test_huge_bounds_are_bounded_and_negative_coordinates_work(self):
        index = RoutingIndex()
        wide, negative = object(), object()
        index.add(wide, QRectF(-1e9, -1e9, 2e9, 2e9))
        index.add(negative, QRectF(-400, -400, 10, 10))
        self.assertIn(negative, index.items(QRectF(-410, -410, 30, 30)))
        self.assertIn(wide, index.items(QRectF(0, 0, 10, 10)))
        self.assertLess(len(index.buckets), 10)
