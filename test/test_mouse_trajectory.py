import random
from unittest.mock import Mock, patch

import pytest

from instructions.common import actions
from instructions.common.mouse_trajectory import TRAJECTORIES, trajectory
from instructions.models import CommandRecord, ExecutionContext, InstructionDraft
from instructions.键鼠.悬停后点击.悬停后点击 import InstructionExecutor


@pytest.mark.parametrize('end', [(500, 100), (100, 500), (500, 500), (-300, -200), (100, 100)])
def test_curve_endpoints_continuity_randomness_and_bounds(end):
    start = (100, 100)
    paths = [list(trajectory(start, end, 100, TRAJECTORIES[1], random.Random(seed))) for seed in (1, 2)]
    for path in paths:
        assert path[-1] == end and len(path) == 100
        assert max(max(abs(a-b) for a,b in zip(p,q)) for p,q in zip([start]+path,path)) < 20
    if end != start:
        assert paths[0] != paths[1]
        dx, dy = end[0]-start[0], end[1]-start[1]
        assert any((x-start[0])*dy != (y-start[1])*dx for x,y in paths[0])
    bounded = list(trajectory((0,0), (1919,1079), 100, TRAJECTORIES[1], random.Random(3), (0,0,1919,1079)))
    assert all(0 <= x <= 1919 and 0 <= y <= 1079 for x,y in bounded)


def test_linear_compatibility_and_bad_mode():
    assert list(trajectory((0,0),(10,20), 2)) == [(5,10),(10,20)]
    assert list(trajectory((1,2),(3,4),1,TRAJECTORIES[1])) == [(3,4)]
    with pytest.raises(ValueError):
        list(trajectory((0,0),(10,20),2,'bad'))


class HoverMenu:
    """Virtual auto-hide menu: enough hover time, held-free continuous movement."""
    def __init__(self):
        self.time = 0
        self.position = None
        self.open = False
        self.moves = []
        self.clicks = []

    def moveTo(self, x, y, **kwargs):
        if self.position is not None:
            assert self.open, 'left before submenu opened'
            assert abs(x-self.position[0]) <= 10
        self.position = (x,y)
        self.moves.append(self.position)

    def wait(self, seconds):
        self.time += seconds
        if self.position == (100,100) and self.time >= 1.49:
            self.open = True

    def click(self, **kwargs):
        assert self.open and self.time >= 2.79
        assert self.position == (300,100)
        self.clicks.append(kwargs)


def hover_command(**overrides):
    return CommandRecord(1, '悬停后点击', {'悬停位置':'100,100', '点击位置':'300,100', **overrides})


def test_hover_default_wait_then_slow_continuous_move_then_click():
    menu = HoverMenu()
    with patch.object(actions,'pyautogui_module',return_value=menu), patch.object(actions,'wait_seconds',side_effect=menu.wait):
        assert InstructionExecutor().execute(ExecutionContext(),hover_command()) == (300,100)
    assert len(menu.moves) == 51
    assert menu.clicks == [{'button':'left', '_pause':False}]
    assert menu.time == pytest.approx(2.8)


@pytest.mark.parametrize('stop_after', [0, .5, 1.7, 2.7])
def test_hover_stop_at_each_stage_never_clicks(stop_after):
    gui = Mock()
    context = ExecutionContext(stop_requested=stop_after == 0)
    elapsed = 0
    def wait(seconds):
        nonlocal elapsed
        elapsed += seconds
        if elapsed >= stop_after:
            context.stop_requested = True
    with patch.object(actions,'pyautogui_module',return_value=gui), patch.object(actions,'wait_seconds',side_effect=wait):
        assert InstructionExecutor().execute(context,hover_command()) is None
    gui.click.assert_not_called()
    gui.mouseDown.assert_not_called()


@pytest.mark.parametrize('action,button,count', [('左键单击','left',1),('左键双击','left',2),('右键单击','right',1),('中键单击','middle',1)])
def test_same_point_and_editable_zero_times(action, button, count):
    gui = Mock()
    with patch.object(actions,'pyautogui_module',return_value=gui), patch.object(actions,'wait_seconds'):
        InstructionExecutor().execute(ExecutionContext(),hover_command(点击位置='100,100', 停留时间=0, 移动秒数=0, 点击前停留=0, 动作=action))
    assert gui.click.call_count == count
    assert gui.click.call_args.kwargs['button'] == button
    gui.mouseDown.assert_not_called()


def test_new_parameters_survive_workbook_roundtrip(tmp_path):
    from graph_repository import GraphRepository
    from 数据库操作 import DatabaseOperation
    db = DatabaseOperation(str(tmp_path / 'mouse.db'))
    repo = GraphRepository(db.db_path)
    repo.add_command(InstructionDraft('鼠标拖拽', {'开始位置':'10,20','结束位置':'200,300','移动轨迹':TRAJECTORIES[1]}))
    repo.add_command(hover_command().to_draft())
    before = repo.snapshot()
    from openpyxl import Workbook
    book = Workbook()
    repo.export_to_workbook(book)
    repo.import_from_workbook(book)
    assert repo.snapshot().commands == before.commands
    repo.validate_graph()
    book.close()
