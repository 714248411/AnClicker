"""Use PyAutoGUI's real fail-safe checks without injecting any OS input."""
import sys
from pathlib import Path
from unittest.mock import patch
sys.path.insert(0, str(Path(__file__).resolve().parents[1]))
import pyautogui as gui
from anclicker.domain.instructions import ExecutionContext, CommandRecord
from anclicker.instructions.键鼠.移动鼠标.executor import InstructionExecutor
from anclicker.execution.human_mouse import move_human

width, height = gui.size()
corners = tuple(gui.FAILSAFE_POINTS)
position = [100, 100]
moves = []
def inject(x, y):
    position[:] = [x, y]
    moves.append((x, y))
def execute(parameters):
    return InstructionExecutor().execute_once(ExecutionContext(), CommandRecord(1, '移动鼠标', dict(parameters, 持续=0)))
with patch.object(gui, 'position', side_effect=lambda *args: tuple(position)), patch.object(gui.platformModule, '_moveTo', side_effect=inject), patch.object(gui, 'PAUSE', 0), patch.object(gui, 'FAILSAFE', True), patch('anclicker.instructions.键鼠.移动鼠标.executor.actions.pyautogui_module', return_value=gui):
    for mode in ('模拟人1（WindMouse）', '模拟人2（BezMouse）', '指定坐标'):
        for corner in corners:
            position[:] = [100, 100]
            moves.clear()
            result = execute({'类型': mode, '方向': '无', '坐标': corner})
            assert result not in corners and moves, (mode, corner, result, moves, (width, height))
            assert not set(moves).intersection(corners)
            assert max(abs(result[i]-corner[i]) for i in (0, 1)) == 1
            execute({'类型': mode, '方向': '无', '坐标': (100, 100)})
            assert tuple(position) == (100, 100)
            assert gui.FAILSAFE is True
    print('PASS real fail-safe: all four corners, both human modes, absolute coordinates and consecutive tests')
    context = ExecutionContext(variables={'目标': (0, 0)})
    assert InstructionExecutor().execute_once(context, CommandRecord(1, '移动鼠标', {'类型': '变量坐标', '变量': '目标', '持续': 0})) == (1, 1)
    with patch('anclicker.instructions.键鼠.移动鼠标.executor.random.randint', side_effect=[width-1, height-1]):
        assert execute({'类型': '随机移动'}) == (width-2, height-2)
    position[:] = [0, 5]
    with patch('anclicker.instructions.键鼠.移动鼠标.executor.random.randint', return_value=500), patch('anclicker.instructions.键鼠.移动鼠标.executor.random.choice', return_value=(0, -500)):
        assert execute({'类型': '随机移动', '随机': '类型2'}) == (1, 1)
    position[:] = [0, 5]
    assert execute({'类型': '直线移动', '方向': '↑', '距离': 5}) == (1, 1)
    print('PASS variable, random and directed movement avoid program-generated corners')
    position[:] = [100, 100]
    with patch('anclicker.execution.human_mouse.mouse_path', return_value=[(-100, -100), (0, 0), (100, 100)]):
        assert move_human(gui, ExecutionContext(), (100, 100), 0, 'wind') == (100, 100)
    position[:] = [0, 0]
    for mode in ('模拟人1（WindMouse）', '指定坐标'):
        try:
            execute({'类型': mode, '方向': '无', '坐标': (100, 100)})
        except gui.FailSafeException:
            pass
        else:
            raise AssertionError('Manual corner emergency stop was bypassed')
    assert gui.FAILSAFE is True
    position[:] = [100, 100]
    moves.clear()
    move_human(gui, ExecutionContext(stop_requested=True), (0, 0), 0, 'wind')
    assert not moves
    print('PASS intermediate edge points, manual fail-safe and cancellation remain effective')
