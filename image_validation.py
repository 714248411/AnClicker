"""Fresh-process image execution using real OpenCV and synthetic screen pixels.

No native screenshots or input: only screen acquisition and output clicks are
substituted. Loading, matching, regions, policies and executors are real.
"""
import json
from pathlib import Path
import tempfile
from unittest.mock import patch, Mock
import numpy as np
from PIL import Image
import pyautogui
from instructions.common import actions
from instructions.models import CommandRecord, ExecutionContext
from instructions.registry import get_instruction_spec


def validate_image_execution(require_fresh=False):
    rng = np.random.default_rng(42)
    pixels = rng.integers(0, 256, (180, 240, 3), dtype=np.uint8)
    screen = Image.fromarray(pixels)
    messages = []
    checks = []
    with tempfile.TemporaryDirectory() as folder:
        directory = Path(folder) / '中文资源 空格'
        directory.mkdir()
        image = directory / '目标按钮.png'
        screen.crop((91, 57, 119, 81)).save(image)
        move, click = Mock(), Mock()
        with patch.object(pyautogui, 'screenshot', side_effect=lambda **kwargs: screen.copy()), \
             patch.object(pyautogui, 'moveTo', move), patch.object(pyautogui, 'click', click):
            base = {'图像路径': str(image), '精度': .99, '灰度': False, '异常': '0', '动作': '左键单击'}
            context = ExecutionContext(output=messages.append, metadata={'project_path': str(directory/'project.xlsx')})
            def execute(type_id, parameters):
                return get_instruction_spec(type_id).create_executor().execute(
                    context, CommandRecord(id=1, type_id=type_id, parameters=parameters,
                                           repeat_count=1, order=0, error_policy='提示异常并暂停'))
            for grayscale in (False, True):
                for area in ('', '(80,40,100,80)', [0,0,0,0], (0,0,0,0)):
                    result = execute('图像点击', dict(base, 灰度=grayscale, 区域=area))
                    assert result == (105,69), (grayscale, area, result, messages)
                    click.assert_called_with(105,69,clicks=1,interval=0.0,button='left')
                    checks.append('match-region-gray')
            result = execute('图像点击', dict(base, 图像路径=image.name, 点击位置='(8,-3)', 动作='右键双击'))
            assert result == (113,66)
            click.assert_called_with(113,66,clicks=2,interval=0.0,button='right')
            checks.append('relative-offset-action')
            assert execute('图像等待', dict(base, 等待类型='等待出现', 超时时间=1)) is True
            checks.append('image-wait')
            assert execute('多图点击', dict(base, 图像路径=str(directory/'missing.png')+'\n'+str(image))) is not None
            checks.append('multiple-images')
            blank = Image.new('RGB', screen.size, 'black')
            click.reset_mock()
            with patch.object(pyautogui, 'screenshot', side_effect=lambda **kwargs: blank.copy()):
                assert actions.locate_image(base, context) is None
                with patch.object(actions, 'image_error_timeout', return_value=(True,0)):
                    assert execute('图像点击', base) is False
                click.assert_not_called()
            checks.append('not-found-no-click')
            # A second quick capture can look very similar to the first one.
            # The exact second image must win over an earlier .8+ screen match.
            target = screen.crop((91, 57, 119, 81))
            changed = np.array(target)
            changed[8:12, 10:14] = 255 - changed[8:12, 10:14]
            second = Image.fromarray(changed)
            second_path = directory / '第二次截图.png'
            second.save(second_path)
            both = screen.copy()
            both.paste(second, (170, 125))
            with patch.object(pyautogui, 'screenshot', side_effect=lambda **kwargs: both.copy()):
                assert execute('图像点击', dict(base, 精度=.8, 图像路径=str(second_path))) == (184, 137)
                click.assert_called_with(184, 137, clicks=1, interval=0.0, button='left')
            checks.append('second-capture-best-match')
            moved = Image.new('RGB', screen.size, 'black')
            moved.paste(target, (170, 125))
            with patch.object(pyautogui, 'screenshot', side_effect=[screen.copy(), moved.copy(), moved.copy()]):
                assert execute('图像点击', base) == (184, 137)
            checks.append('moving-target-recheck')
    return {'checks': checks, 'count':len(checks), 'synthetic_screen':True}


if __name__ == '__main__':
    print(json.dumps(validate_image_execution(require_fresh=True), ensure_ascii=False))
