"""An offscreen virtual mouse target: never sends input to the OS desktop."""
import os
from types import SimpleNamespace
from unittest.mock import patch

os.environ.setdefault('QT_QPA_PLATFORM', 'offscreen')
import pytest
from PySide6.QtCore import QPointF, QRectF, Qt, QEvent
from PySide6.QtGui import QMouseEvent, QPainter, QColor
from PySide6.QtWidgets import QApplication, QWidget, QDialog

from instructions.common import actions
from instructions.models import CommandRecord, ExecutionContext
from instructions.键鼠.鼠标拖拽.鼠标拖拽 import InstructionExecutor, InstructionEditor
from instructions.common.mouse_trajectory import TRAJECTORIES


class DragCanvas(QWidget):
    def __init__(self):
        super().__init__()
        self.resize(480, 360)
        self.box = QRectF(55, 95, 50, 50)
        self.target = QPointF(360, 260)
        self.dragging = False
        self.dropped = False

    def mousePressEvent(self, event):
        self.dragging = event.button() == Qt.LeftButton and self.box.contains(event.position())

    def mouseMoveEvent(self, event):
        if self.dragging and event.buttons() & Qt.LeftButton:
            self.box.moveCenter(event.position())
            self.update()

    def mouseReleaseEvent(self, event):
        self.dropped = self.dragging and self.box.center() == self.target
        self.dragging = False
        self.update()

    def paintEvent(self, event):
        painter = QPainter(self)
        painter.fillRect(self.rect(), QColor('#f4f5f8'))
        painter.setPen(QColor('#444444'))
        painter.drawText(20, 30, 'Virtual drag test - no OS input')
        painter.setPen(QColor('#2675d9'))
        painter.drawRect(QRectF(330, 230, 60, 60))
        painter.fillRect(self.box, QColor('#e3a24a'))
        painter.setPen(QColor('#222222'))
        painter.drawText(20, 330, f'Dropped at target: {self.dropped}')


class VirtualMouse:
    FAILSAFE = True

    def __init__(self, canvas):
        self.canvas = canvas
        self.point = QPointF()
        self.held = False
        self.events = []
        self.on_move = None

    def _event(self, kind, button=Qt.NoButton):
        event = QMouseEvent(kind, self.point, self.point, button,
                            Qt.LeftButton if self.held else Qt.NoButton, Qt.NoModifier)
        QApplication.sendEvent(self.canvas, event)

    def moveTo(self, x, y, **kwargs):
        self.point = QPointF(x, y)
        self.events.append(('move', x, y, self.held))
        if self.on_move:
            self.on_move()
        self._event(QEvent.MouseMove)

    def mouseDown(self, button, **kwargs):
        assert button == 'left'
        self.held = True
        self.events.append(('down',))
        self._event(QEvent.MouseButtonPress, Qt.LeftButton)

    def mouseUp(self, button, **kwargs):
        assert button == 'left'
        self.held = False
        self.events.append(('up',))
        self._event(QEvent.MouseButtonRelease, Qt.LeftButton)


def command(**extra):
    return CommandRecord(1, '鼠标拖拽', {'开始位置':'80,120', '结束位置':'360,260', '移动速度':.1, **extra})


@pytest.fixture
def virtual_desktop():
    app = QApplication.instance() or QApplication([])
    canvas = DragCanvas()
    canvas.show()
    app.processEvents()
    mouse = VirtualMouse(canvas)
    with patch.object(actions, 'pyautogui_module', return_value=mouse), patch.object(actions, 'wait_seconds'):
        yield app, canvas, mouse
    canvas.hide()
    canvas.deleteLater()
    app.processEvents()


@pytest.mark.parametrize('duration', [0, .1, .5])
@pytest.mark.parametrize('mode', TRAJECTORIES)
def test_drag_holds_and_reaches_exact_destination(virtual_desktop, duration, mode):
    _, canvas, mouse = virtual_desktop
    context = ExecutionContext()
    InstructionExecutor().execute(context, command(移动速度=duration, 移动轨迹=mode))
    assert canvas.dropped
    assert canvas.box.center() == QPointF(360, 260)
    assert mouse.events[0] == ('move', 80, 120, False)
    assert mouse.events[1] == ('down',)
    assert mouse.events[-1] == ('up',)
    assert all(event[-1] for event in mouse.events[2:-1])
    assert not mouse.held and not context.metadata['recorded_buttons']


@pytest.mark.parametrize('mode', TRAJECTORIES)
def test_stopping_mid_drag_releases_button(virtual_desktop, mode):
    _, canvas, mouse = virtual_desktop
    context = ExecutionContext()
    def stop():
        if mouse.held:
            context.stop_requested = True
    mouse.on_move = stop
    assert InstructionExecutor().execute(context, command(移动轨迹=mode)) is None
    assert not canvas.dropped and not mouse.held
    assert mouse.events[-1] == ('up',)
    assert not context.metadata['recorded_buttons']


@pytest.mark.parametrize('mode', TRAJECTORIES)
def test_move_error_releases_and_restores_failsafe(virtual_desktop, mode):
    _, _, mouse = virtual_desktop
    def fail():
        if mouse.held:
            raise RuntimeError('virtual failure')
    mouse.on_move = fail
    with pytest.raises(RuntimeError, match='virtual failure'):
        InstructionExecutor().execute(ExecutionContext(), command(移动轨迹=mode))
    assert not mouse.held and mouse.FAILSAFE is True
    assert mouse.events[-1] == ('up',)


def test_stop_before_start_never_presses(virtual_desktop):
    _, _, mouse = virtual_desktop
    InstructionExecutor().execute(ExecutionContext(stop_requested=True), command())
    assert mouse.events == []


@pytest.mark.parametrize('accepted', [True, False])
def test_editor_selects_target_not_own_button(virtual_desktop, accepted):
    app, _, _ = virtual_desktop
    editor = InstructionEditor()
    editor.show()
    app.processEvents()
    previous = editor._controls['开始位置'].text()
    selector = SimpleNamespace(point=(-120, 280), capture_error=None,
                               exec=lambda: QDialog.Accepted if accepted else QDialog.Rejected,
                               deleteLater=lambda: None)
    with patch('instructions.common.editor._PointSelectionDialog', return_value=selector):
        editor._run_auxiliary('开始位置')
    assert editor._controls['开始位置'].text() == ('-120,280' if accepted else previous)
    assert editor.isVisible()
    editor.hide()
    editor.deleteLater()
