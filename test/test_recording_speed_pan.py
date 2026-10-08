import os
os.environ.setdefault('QT_QPA_PLATFORM', 'offscreen')
import tempfile
import unittest
from types import SimpleNamespace
from unittest.mock import Mock, patch
from qt_compat.QtCore import QObject, QPointF, Qt, QEvent, Signal
from qt_compat.QtGui import QMouseEvent
from qt_compat.QtWidgets import QApplication, QGraphicsScene, QMainWindow, QTableWidget, QLabel, QPlainTextEdit
from input_recording import InputEvent, events_to_drafts, recording_at_speed
from recording_view import RecordingView
from graph_repository import GraphRepository
from view_workspace import ViewWorkspace
from node_editor.view import NodeView
from 数据库操作 import DatabaseOperation


class SpeedAndPanTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.app = QApplication.instance() or QApplication([])

    def drafts(self):
        return events_to_drafts([InputEvent(10, 'button', (10,20,'left',True)),
                                InputEvent(15, 'move', (100,200)),
                                InputEvent(20, 'button', (100,200,'left',False))])

    def test_speed_scales_timeline_not_order_coordinates_or_original(self):
        original = self.drafts()
        for speed in (0.1, 0.5, 1, 1.25, 2, 10):
            with self.subTest(speed=speed):
                scaled = recording_at_speed(original, speed)
                self.assertEqual([d.type_id for d in scaled], [d.type_id for d in original])
                self.assertEqual([d.parameters['录制时间'] for d in scaled], [0,5/speed,10/speed])
                for old, new in zip(original, scaled):
                    self.assertEqual({k:v for k,v in old.parameters.items() if k!='录制时间'},
                                     {k:v for k,v in new.parameters.items() if k!='录制时间'})
        self.assertEqual([d.parameters['录制时间'] for d in original], [0,5,10])

    def test_invalid_speed_rejected_and_empty_supported(self):
        for speed in (0,-1,float('nan'),float('inf'),'invalid'):
            with self.assertRaises(ValueError): recording_at_speed(self.drafts(),speed)
        self.assertEqual(recording_at_speed([],1.25),[])

    def test_zero_timing_stays_zero_and_copies_are_independent(self):
        drafts=events_to_drafts([InputEvent(0,'scroll',(1,2,0,-1))],False)
        scaled=recording_at_speed(drafts,1.25)
        scaled[0].parameters['录制滚轮'][1]=10
        self.assertEqual(drafts[0].parameters['录制滚轮'],[0,-1])
        self.assertEqual(scaled[0].parameters['录制时间'],0)

    def test_both_buttons_persist_and_sync_without_duplicate_write(self):
        class Workspace(QObject):
            graphFinalized=Signal(bool)
            statusMessage=Signal(str)
        for use_speed in (False,True):
            with self.subTest(use_speed=use_speed), tempfile.TemporaryDirectory() as directory:
                db=DatabaseOperation(os.path.join(directory,'test.db'))
                repository=GraphRepository(db.db_path)
                workspace=Workspace()
                workspace.repository=repository
                workspace.reload_graph=Mock()
                window=QMainWindow()
                window.workspace=workspace
                window.command_thread=SimpleNamespace(isRunning=lambda:False)
                projection=ViewWorkspace.__new__(ViewWorkspace)
                projection.window=SimpleNamespace(db=db,workspace=workspace)
                projection.command_table,projection.table_state=QTableWidget(0,7),QLabel()
                projection.code_editor,projection.code_status=QPlainTextEdit(),QLabel()
                projection._loading_code=projection._code_dirty=False
                workspace.graphFinalized.connect(lambda _, p=projection:p.refresh_table())
                workspace.graphFinalized.connect(lambda _, p=projection:p._sync_code_if_needed(force=True))
                widget=RecordingView(window)
                self.assertEqual(widget.speed.value(),1.25)
                self.assertFalse(widget.auto_option.isChecked())
                widget.drafts=self.drafts()
                widget.speed.setValue(2.5)
                widget.update_buttons()
                with patch('recording_view.QMessageBox.warning',side_effect=AssertionError('Unexpected write error')):
                    (widget.speed_write_button if use_speed else widget.write_button).click()
                    widget.write_at_speed() # Must not append this recording twice.
                expected=[0,2,4] if use_speed else [0,5,10]
                self.assertEqual([c.parameters['录制时间'] for c in repository.list_commands()],expected)
                self.assertEqual(projection.command_table.rowCount(),3)
                self.assertIn('鼠标拖拽',projection.code_editor.toPlainText())
                self.assertEqual(len(repository.snapshot().nodes),5)
                repository.validate_graph()
                self.assertFalse(widget.speed_write_button.isEnabled())
                self.assertFalse(widget.write_button.isEnabled())
                self.assertEqual(widget.drafts[-1].parameters['录制时间'],10)
                window.close()
                widget.close()

    def make_view(self):
        scene=QGraphicsScene()
        scene.setSceneRect(-10000,-10000,20000,20000)
        view=NodeView(scene)
        view.resize(600,400)
        view.show()
        view.centerOn(0,0)
        self.app.processEvents()
        self.addCleanup(view.close)
        return scene,view

    def send(self,view,kind,pos,button,buttons):
        event=QMouseEvent(kind,QPointF(*pos),QPointF(*pos),button,buttons,Qt.KeyboardModifier.NoModifier)
        QApplication.sendEvent(view.viewport(),event)

    def test_middle_pan_tracks_mouse_in_screen_pixels_at_any_zoom(self):
        scene,view=self.make_view()
        for zoom in (0.5,1,2):
            view._set_zoom(zoom)
            view.centerOn(0,0)
            start=view.horizontalScrollBar().value()
            self.send(view,QEvent.Type.MouseButtonPress,(300,200),Qt.MiddleButton,Qt.MiddleButton)
            for x in (290,280,260,220):
                self.send(view,QEvent.Type.MouseMove,(x,200),Qt.NoButton,Qt.MiddleButton)
            self.assertEqual(view.horizontalScrollBar().value(),start+80)
            self.send(view,QEvent.Type.MouseButtonRelease,(220,200),Qt.MiddleButton,Qt.NoButton)
            self.assertFalse(view._panning)
            self.assertFalse(view._pan_moved) # Must not suppress the next right-click menu.

    def test_fractional_movements_accumulate_and_other_release_does_not_end_pan(self):
        scene,view=self.make_view()
        start=view.horizontalScrollBar().value()
        self.send(view,QEvent.Type.MouseButtonPress,(300,200),Qt.MiddleButton,Qt.MiddleButton)
        for step in range(1,31):
            self.send(view,QEvent.Type.MouseMove,(300-step*0.2,200),Qt.NoButton,Qt.MiddleButton)
        self.assertEqual(view.horizontalScrollBar().value(),start+6)
        self.send(view,QEvent.Type.MouseButtonRelease,(294,200),Qt.LeftButton,Qt.MiddleButton)
        self.assertTrue(view._panning)
        self.send(view,QEvent.Type.MouseButtonRelease,(294,200),Qt.MiddleButton,Qt.NoButton)
        self.assertFalse(view._panning)

    def test_middle_on_item_does_not_pan_and_focus_loss_cancels(self):
        scene,view=self.make_view()
        item=scene.addRect(-50,-50,100,100)
        pos=view.mapFromScene(item.sceneBoundingRect().center())
        self.send(view,QEvent.Type.MouseButtonPress,(pos.x(),pos.y()),Qt.MiddleButton,Qt.MiddleButton)
        self.assertFalse(view._panning)
        self.send(view,QEvent.Type.MouseButtonRelease,(pos.x(),pos.y()),Qt.MiddleButton,Qt.NoButton)
        self.send(view,QEvent.Type.MouseButtonPress,(30,30),Qt.MiddleButton,Qt.MiddleButton)
        self.assertTrue(view._panning)
        from qt_compat.QtGui import QFocusEvent
        view.focusOutEvent(QFocusEvent(QEvent.Type.FocusOut))
        self.assertFalse(view._panning)
