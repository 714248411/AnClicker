import os
os.environ.setdefault('QT_QPA_PLATFORM', 'offscreen')
from pathlib import Path
import socket
from unittest.mock import Mock, patch

import pytest
from PIL import Image, ImageDraw, ImageFont
from instructions.models import CommandRecord, ExecutionContext, InstructionDraft
from instructions.registry import get_instruction_spec
from instructions.common.local_ocr_instruction import OCR_TYPES, fields_for
from local_ocr import OcrSession, OcrCancelled, validated_rows, find_matches
from local_ocr_worker import RapidBackend, normalize_wechat


def row(text='开始运行', x=10, y=20, score=.99):
    return {'text': text, 'score': score, 'box': [[x,y],[x+100,y],[x+100,y+40],[x,y+40]]}


def execute(name, parameters, rows, context=None):
    context = context or ExecutionContext()
    service = rows if callable(rows) else lambda **kwargs: rows
    context.services = dict(context.services, 本地OCR=service)
    result = get_instruction_spec(name).create_executor().execute(context, CommandRecord(1, name, parameters))
    return result, context


def test_exact_click_screen_offset_and_variables():
    with patch('instructions.common.actions.mouse_action') as click:
        value, context = execute('OCR精准找字点击', {'区域': '200,300,400,500', '目标文字': '开始运行',
            '点击位置': '(5,-5)', '变量': '位置'}, [row('开始运行吧'), row()])
    assert value == [260, 340]
    click.assert_called_once_with('左键单击', 265, 335)
    assert context.variables['位置'] == [260, 340]
    assert context.variables['位置_X'] == 260 and context.variables['位置_Y'] == 340
    assert len(context.variables['位置_详情']) == 1


def test_fuzzy_threshold_contains_and_normalization():
    rows = validated_rows([row('ＡＢＣ 123'), row('开始运仃', y=70)])
    assert find_matches(rows, 'abc123', '精准')[0]['text'] == 'ＡＢＣ 123'
    assert find_matches(rows, '开始运行', '模糊', .7)[0]['text'] == '开始运仃'
    assert not find_matches(rows, '开始运行', '模糊', .9)
    assert not find_matches(rows, 'ABC123', '精准', ignore_case=False, ignore_spaces=False)


def test_range_coordinates_negative_origin_second_match():
    value, context = execute('OCR范围找字', {'区域': '-500,100,400,300', '目标文字': '运行',
        '第几个': 2}, [row(y=80), row(y=20)])
    assert value == [-440, 200]


def test_empty_result_clears_stale_coordinate_and_does_not_click():
    context = ExecutionContext(variables={'OCR坐标': [100, 100], 'OCR坐标_X': 100})
    with patch('instructions.common.actions.mouse_action') as click:
        result, context = execute('OCR精准找字点击', {'目标文字': '开始', '未找到': '返回空值'}, [], context)
    assert result is None and context.variables['OCR坐标'] is None
    assert context.variables['OCR坐标_X'] is None
    click.assert_not_called()


def test_stop_after_recognition_prevents_late_click_or_variable_write():
    context = ExecutionContext()
    def recognize(**kwargs):
        context.stop_requested = True
        return [row()]
    with patch('instructions.common.actions.mouse_action') as click:
        value, context = execute('OCR精准找字点击', {'目标文字': '开始运行'}, recognize, context)
    assert value is None and not context.variables
    click.assert_not_called()


@pytest.mark.parametrize('name,results,expected', [
    ('OCR等待文字出现', [[], [row()], [], [row()], [row()]], [60, 40]),
    ('OCR等待文字消失', [[row()], [], [row()], [], []], True),
])
def test_wait_requires_consecutive_observations(name, results, expected):
    context = ExecutionContext(metadata={'wait_interruptibly': lambda seconds, context: True})
    service = Mock(side_effect=results)
    result, context = execute(name, {'目标文字': '开始运行'}, service, context)
    assert result == expected and service.call_count == 5


def test_wait_timeout_and_low_confidence_do_not_report_success():
    context = ExecutionContext(metadata={'wait_interruptibly': lambda seconds, context: True})
    with pytest.raises(TimeoutError):
        execute('OCR等待文字出现', {'目标文字': '开始运行', '等待超时': .1}, [row(score=.2)], context)


@pytest.mark.parametrize('parameters', [{'相似度': float('nan')}, {'第几个': 0},
    {'第几个': 1.5}, {'置信度': 1.1}, {'识别超时': 0}, {'区域': '0,0,-5,10'}, {'引擎': 'cloud'}])
def test_invalid_parameters_fail_without_screenshot(parameters):
    with patch('instructions.common.actions.pyautogui_module') as gui, pytest.raises(ValueError):
        execute('OCR模糊找字返回坐标', dict(目标文字='test', **parameters), [])
    gui.assert_not_called()


def test_wechat_two_adapter_formats_and_error():
    expected = [[2.,3.],[12.,3.],[12.,13.],[2.,13.]]
    item = {'text': 'test', 'left': 2, 'top': 3, 'right': 12, 'bottom': 13, 'rate': .8}
    assert normalize_wechat({'ocr_response': [item]})[0]['box'] == expected
    assert normalize_wechat({'ocr_response': [item]})[0]['score'] == .8
    assert normalize_wechat({'ocrResult': [{'text': 'test', 'location': item}]})[0]['box'] == expected
    with pytest.raises(ValueError):
        normalize_wechat({'unknown': []})
    with pytest.raises(RuntimeError):
        normalize_wechat({'ocr_response': [], 'errcode': 1})


@pytest.fixture
def text_image(tmp_path):
    image = Image.new('RGB', (700, 140), 'white')
    draw = ImageDraw.Draw(image)
    draw.text((20, 35), 'An Clicker 12345', font=ImageFont.load_default(size=48), fill='black')
    path = tmp_path / '离线文字.png'
    image.save(path)
    return path


def test_real_rapid_model_offline_unicode_path(text_image, monkeypatch):
    def forbid_network(*args, **kwargs):
        raise AssertionError('Offline OCR must not connect to the network')
    monkeypatch.setattr(socket.socket, 'connect', forbid_network)
    monkeypatch.setattr(socket, 'create_connection', forbid_network)
    backend = RapidBackend()
    rows = validated_rows(backend.recognize(str(text_image)))
    assert '12345' in ''.join(r['text'] for r in rows)
    assert all(0 <= r['center'][0] < 700 for r in rows)


def test_real_worker_and_file_instruction(text_image):
    context = ExecutionContext()
    parameters = {'图像路径': str(text_image), '变量': '识别文字'}
    result = get_instruction_spec('OCR文字提取').create_executor().execute(
        context, CommandRecord(1, 'OCR文字提取', parameters))
    assert '12345' in result and result == context.variables['识别文字']


def test_worker_timeout_kills_only_own_process(text_image):
    with OcrSession() as session:
        with pytest.raises(TimeoutError):
            session.recognize(text_image, 'RapidOCR', {}, ExecutionContext(), .001)
        process = session.process
    assert process.poll() is not None


def test_unconfigured_wechat_returns_clear_error(text_image):
    with OcrSession() as session, pytest.raises(RuntimeError, match='微信OCR文件路径'):
        session.recognize(text_image, '微信OCR', {}, ExecutionContext(), 15)


def test_six_modules_saved_roundtrip(tmp_path):
    from 数据库操作 import DatabaseOperation
    from graph_repository import GraphRepository
    db = DatabaseOperation(str(tmp_path / 'ocr.db'))
    repo = GraphRepository(db.db_path)
    for name in OCR_TYPES:
        params = {f.key: f.default for f in fields_for(name)}
        if '目标文字' in params:
            params['目标文字'] = 'test'
        if name in ('OCR范围找字', '截图OCR', 'OCR复制'):
            params['区域'] = '0,0,200,100'
        repo.add_command(InstructionDraft(name, params))
    from openpyxl import Workbook
    workbook = Workbook()
    repo.export_to_workbook(workbook)
    other = GraphRepository(DatabaseOperation(str(tmp_path / 'new.db')).db_path)
    other.import_from_workbook(workbook)
    assert [c.type_id for c in other.list_commands()] == list(OCR_TYPES)
    assert len(other.snapshot().nodes) == len(OCR_TYPES) + 2


def test_ocr_copy_then_paste_without_variables():
    import pyperclip
    context = ExecutionContext(metadata={'wait_interruptibly': lambda seconds, context: True})
    gui = Mock()
    with patch.object(pyperclip, 'copy') as copy, patch('instructions.common.actions.pyautogui_module', return_value=gui):
        text, context = execute('OCR复制', {'区域': '0,0,100,100'}, [row('待粘贴内容')], context)
        assert text == '待粘贴内容' and not context.variables
        copy.assert_called_once_with(text)
        result, _ = execute('OCR粘贴', {}, [], context)
        assert result == text
        gui.hotkey.assert_called_once()


def test_failed_ocr_cannot_paste_previous_result():
    context = ExecutionContext(metadata={'last_ocr_text': 'stale'})
    with pytest.raises(ValueError):
        execute('截图OCR', {'区域': '0,0,100,100'}, [], context)
    assert context.metadata['last_ocr_text'] is None
    with pytest.raises(ValueError), patch('instructions.common.actions.pyautogui_module') as gui:
        execute('OCR粘贴', {'粘贴前等待': 0}, [], context)
    gui.assert_not_called()


def test_region_click_second_nearest_with_absolute_anchor():
    with patch('instructions.common.actions.mouse_action') as click:
        value, context = execute('OCR点击识别区域', {
            '区域': '200,300,400,400', '排序方式': '离锚点最近',
            '中心锚点': '260,400', '第几个': 2, '点击位置': '3,-2'},
            [row('远', y=200), row('近', y=80), row('第二', y=120)])
    assert value == [260, 440]
    click.assert_called_once_with('左键单击', 263, 438)
    assert context.variables['OCR坐标_区域'][0] == [210, 420]


def test_range_center_anchor_and_optional_click():
    with patch('instructions.common.actions.mouse_action') as click:
        value, _ = execute('OCR范围找字', {'区域': '-500,100,400,300',
            '目标文字': '运行', '排序方式': '离锚点最近', '找到后': '点击区域'},
            [row(y=20), row(x=140, y=120)])
    assert value == [-310, 240]
    click.assert_called_once_with('左键单击', -310, 240)


def test_region_return_all_text_boxes_without_click():
    with patch('instructions.common.actions.mouse_action') as click:
        value, _ = execute('OCR识别区域返回坐标', {'第几个': 2}, [row('甲'), row('乙', y=100)])
    assert value == [60, 120]
    click.assert_not_called()


def test_nearest_without_range_or_anchor_rejected():
    with pytest.raises(ValueError, match='锚点'):
        execute('OCR识别区域返回坐标', {'排序方式': '离锚点最近'}, [row()])
