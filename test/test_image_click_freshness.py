"""Moving-target regressions with real template matching and synthetic frames.

Only screen acquisition and mouse output are replaced; no desktop input is sent.
"""
from types import SimpleNamespace
from unittest.mock import Mock, patch

import numpy as np
import pytest
from PIL import Image
import pyautogui

from instructions.common import actions
from instructions.models import CommandRecord, ExecutionContext
from instructions.registry import get_instruction_spec


@pytest.fixture
def screen(tmp_path):
    pixels = np.random.default_rng(17).integers(0, 256, (22, 30, 3), dtype=np.uint8)
    target = Image.fromarray(pixels)
    path = tmp_path / '移动按钮.png'
    target.save(path)

    class Screen:
        position = (40, 50)
        captures = 0
        after_capture = None
        after_move = None
        after_click = None

        def capture(self, **kwargs):
            frame = Image.new('RGB', (360, 240), '#202020')
            if self.position is not None:
                frame.paste(target, (self.position[0] - 15, self.position[1] - 11))
            self.captures += 1
            if self.after_capture:
                self.after_capture(self.captures)
            return frame

        def move(self, *args, **kwargs):
            if self.after_move:
                self.after_move()

        def click(self, *args, **kwargs):
            if self.after_click:
                self.after_click()

        def execute(self, type_id='图像点击', context=None, repeat=1, **parameters):
            params = {'图像路径': str(path), '精度': .99, '异常': '自动略过'}
            params.update(parameters)
            return get_instruction_spec(type_id).create_executor().execute(
                context or ExecutionContext(), CommandRecord(1, type_id, params, repeat_count=repeat))

    state = Screen()
    with patch.object(pyautogui, 'screenshot', side_effect=state.capture), \
         patch.object(pyautogui, 'moveTo', side_effect=state.move) as move, \
         patch.object(pyautogui, 'click', side_effect=state.click) as click:
        state.move_mock = move
        state.click_mock = click
        yield state


@pytest.mark.parametrize('type_id', ['图像点击', '多图点击'])
@pytest.mark.parametrize('move_at', ['capture', 'move'])
def test_target_moves_before_click(screen, type_id, move_at):
    def relocate(*args):
        screen.position = (240, 150)
    setattr(screen, 'after_' + move_at, relocate)
    screen.execute(type_id)
    assert screen.click_mock.call_count == 1
    assert screen.click_mock.call_args.args == (240, 150)
    assert screen.captures >= 3


@pytest.mark.parametrize('type_id', ['图像点击', '多图点击'])
def test_disappeared_target_is_never_clicked(screen, type_id):
    screen.after_move = lambda: setattr(screen, 'position', None)
    assert screen.execute(type_id) is False
    screen.click_mock.assert_not_called()


def test_disappeared_target_keeps_error_policy(screen):
    screen.after_move = lambda: setattr(screen, 'position', None)
    with pytest.raises(FileNotFoundError):
        screen.execute(异常='0')
    screen.click_mock.assert_not_called()


def test_repeated_instruction_recaptures_target(screen):
    screen.after_click = lambda: setattr(screen, 'position', (240, 150))
    assert screen.execute(repeat=2) == (240, 150)
    assert [call.args for call in screen.click_mock.call_args_list] == [(40, 50), (240, 150)]


def test_continuously_moving_target_is_bounded_without_click(screen):
    def move_target(*args):
        screen.position = (240, 150) if screen.position == (40, 50) else (40, 50)
    screen.after_move = move_target
    assert screen.execute() is False
    screen.click_mock.assert_not_called()
    assert screen.captures <= 10


def test_stop_during_recheck_does_not_click(screen):
    context = ExecutionContext()
    def stop(captures):
        if captures == 2:
            context.stop_requested = True
    screen.after_capture = stop
    assert screen.execute(context=context) is False
    screen.click_mock.assert_not_called()


def test_move_only_tracks_latest_position_without_click(screen):
    screen.after_capture = lambda _: setattr(screen, 'position', (240, 150))
    assert screen.execute(动作='仅移动鼠标') == (240, 150)
    assert screen.move_mock.call_args.args == (240, 150)
    screen.click_mock.assert_not_called()


def test_offset_and_double_click_follow_relocated_target(screen):
    screen.after_capture = lambda _: setattr(screen, 'position', (240, 150))
    assert screen.execute(动作='右键双击', 点击位置='(8,-3)') == (248, 147)
    screen.click_mock.assert_called_once_with(248, 147, clicks=2, interval=0.0, button='right')


def test_no_default_move_pause_between_confirmation_and_click(screen):
    assert screen.execute() == (40, 50)
    screen.move_mock.assert_called_once_with(40, 50, _pause=False)
    assert screen.captures == 2


def test_pause_invalidates_frame_even_when_resumed_before_match_returns(screen):
    from PySide6.QtCore import QMutex, QWaitCondition
    from main_work import CommandThread
    context = ExecutionContext()
    worker = SimpleNamespace(start_state=True, is_paused=False, _active_context=context,
                             mutex=QMutex(), condition=QWaitCondition())
    def pause_and_relocate(captures):
        if captures == 2:
            CommandThread.pause(worker)
            screen.position = (240, 150)
            CommandThread.resume(worker)
    screen.after_capture = pause_and_relocate
    assert screen.execute(context=context) == (240, 150)
    assert screen.click_mock.call_args.args == (240, 150)
    assert screen.captures >= 4


def test_pause_wait_after_capture_forces_new_frame(screen):
    from PySide6.QtCore import QMutex, QWaitCondition
    from main_work import CommandThread
    context = ExecutionContext()
    worker = SimpleNamespace(start_state=True, is_paused=False, _active_context=context,
                             mutex=QMutex(), condition=QWaitCondition())
    def checkpoint(seconds, actual):
        if screen.captures == 2 and screen.position == (40, 50):
            CommandThread.pause(worker)
            screen.position = (240, 150)
            CommandThread.resume(worker)
        return True
    context.metadata['wait_interruptibly'] = checkpoint
    assert screen.execute(context=context) == (240, 150)
    assert screen.click_mock.call_args.args == (240, 150)


def test_random_offset_is_chosen_once_and_follows_moving_target(screen):
    screen.after_capture = lambda _: setattr(screen, 'position', (240, 150))
    with patch.object(actions.random, 'randint', side_effect=lambda low, high: high) as randint:
        assert screen.execute(点击位置='(随机,随机)') == (254, 160)
    assert randint.call_count == 2
    assert screen.click_mock.call_args.args == (254, 160)


def test_multiple_images_can_fall_through_when_first_target_disappears(screen, tmp_path):
    second = tmp_path / '第二按钮.png'
    # Same pixels in another resource: first candidate disappears, then reappears
    # for the next template. The first stale candidate must never be clicked.
    source = tmp_path / '移动按钮.png'
    second.write_bytes(source.read_bytes())
    def vanish_once():
        if screen.captures == 1:
            screen.position = None
    def reappear(captures):
        if captures == 2:
            screen.position = (240, 150)
    screen.after_move = vanish_once
    screen.after_capture = reappear
    assert screen.execute('多图点击', 图像路径=f'{source}\n{second}') == str(second)
    assert screen.click_mock.call_count == 1
    assert screen.click_mock.call_args.args == (240, 150)


@pytest.mark.parametrize('disappears', [False, True])
def test_image_information_entry_uses_confirmed_position(screen, disappears):
    workbook = SimpleNamespace(close=Mock())
    clipboard = SimpleNamespace(copy=Mock())
    screen.after_move = lambda: setattr(screen, 'position', None if disappears else (240, 150))
    with patch.object(actions, 'workbook_cell', return_value=(workbook, None, SimpleNamespace(value='内容'))), \
         patch.dict('sys.modules', {'pyperclip': clipboard}), \
         patch.object(pyautogui, 'hotkey') as paste:
        result = screen.execute('信息录入')
    if disappears:
        assert result is False
        screen.click_mock.assert_not_called()
        clipboard.copy.assert_not_called()
        paste.assert_not_called()
    else:
        assert result == '内容'
        screen.click_mock.assert_called_once_with(240, 150, clicks=3, interval=0.0, button='left')
        clipboard.copy.assert_called_once_with('内容')
