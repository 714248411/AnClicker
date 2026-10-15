"""Instruction execution implementation."""
from __future__ import annotations
from anclicker.instructions.common import actions
from pathlib import Path
import time
from anclicker.domain.instruction_fields.local_ocr_instruction import REGION_TYPES
import math
from anclicker.platform.local_ocr import find_matches
from anclicker.domain.instruction_fields.local_ocr_instruction import TEXT_TYPES
from anclicker.platform.local_ocr import validated_rows
from anclicker.platform.local_ocr import OcrSession
from tempfile import TemporaryDirectory
from anclicker.platform.local_ocr import OcrCancelled
from anclicker.domain.instruction_fields.local_ocr_instruction import fields_for
from anclicker.domain.instruction_fields.local_ocr_instruction import CLICK_TYPES
from anclicker.instructions.common import InstructionExecutorBase

from anclicker._imports import DeferredImports as _DeferredImports

# Dependencies declared here retain their existing on-demand loading boundaries.
_module_imports = _DeferredImports(globals(), {
    'pyperclip': ('import', 'pyperclip', (), False),
    'sys': ('import', 'sys', (), False),
    'TEMP_FOLDER': ('from', 'anclicker.app.paths', ('TEMP_FOLDER',), 0),
})


def validate(name, parameters):
    defaults = {f.key: f.default for f in fields_for(name)}
    defaults.update(parameters)
    if name == 'OCR点击识别区域' and '点击来源' not in parameters:
        defaults['点击来源'] = '重新识别'
        defaults['变量'] = parameters.get('变量', 'OCR坐标')
    for key in ('微信OCR路径', '微信运行目录', '微信接口目录'):
        defaults.pop(key, None)
    for field in fields_for(name):
        value = defaults[field.key]
        if field.required and (not str(value).strip()):
            raise ValueError(f'{field.label}不能为空')
        if field.kind == 'choice' and value not in field.choices:
            raise ValueError(f'{field.label}不是有效选项')
        if field.kind in ('float', 'int'):
            number = float(value)
            if not math.isfinite(number) or not field.minimum <= number <= field.maximum:
                raise ValueError(f'{field.label}超出有效范围')
            if field.kind == 'int' and number != int(number):
                raise ValueError(f'{field.label}必须为整数')
            defaults[field.key] = int(number) if field.kind == 'int' else number
    if name == 'OCR粘贴':
        return defaults
    region = actions.region(defaults['区域'])
    if name in ('OCR范围找字', '截图OCR', 'OCR复制') and region is None:
        raise ValueError('范围找字必须设置有效区域')
    if region and (region[2] <= 0 or region[3] <= 0):
        raise ValueError('识别区域宽高必须大于零')
    if name == 'OCR文字提取' and defaults.get('图像路径') and region:
        raise ValueError('读取图片时请清空屏幕区域；裁剪后图片可直接识别。')
    if name in CLICK_TYPES:
        actions.point(defaults['点击位置'])
    if defaults.get('中心锚点', '').strip():
        anchor = actions.point(defaults['中心锚点'])
        if not all((math.isfinite(float(v)) for v in anchor)):
            raise ValueError('中心锚点必须是有限坐标')
    elif defaults.get('排序方式') == '离锚点最近' and (not region):
        raise ValueError('就近识别请设置识别范围或屏幕中心锚点')
    return defaults

def _write_result(context, parameters, value, matches):
    name = parameters['变量']
    context.metadata['last_ocr_result'] = {'value': value, 'matches': matches}
    context.set_variable(name, value)
    context.set_variable(name + '_详情', matches)
    point = value if isinstance(value, list) and len(value) == 2 else None
    context.set_variable(name + '_X', point[0] if point else None)
    context.set_variable(name + '_Y', point[1] if point else None)
    context.set_variable(name + '_区域', matches[parameters.get('第几个', 1) - 1]['box'] if point and len(matches) >= parameters.get('第几个', 1) else None)
    return value

def order_matches(matches, parameters, region):
    """Distance uses absolute screen coordinates, after crop offset is applied."""
    if parameters.get('排序方式') != '离锚点最近':
        return matches
    anchor = parameters.get('中心锚点', '').strip()
    (x, y) = actions.point(anchor) if anchor else (region[0] + region[2] / 2, region[1] + region[3] / 2)
    return sorted(matches, key=lambda row: (row['center'][0] - x) ** 2 + (row['center'][1] - y) ** 2)

def paste_text(context, text):
    if not isinstance(text, str) or not text:
        raise ValueError('没有可粘贴的OCR文字；请先识别/复制文字。')
    if not actions.wait_interruptibly(context, 0):
        return None
    pyperclip = _module_imports.load('pyperclip')
    sys = _module_imports.load('sys')
    pyperclip.copy(text)
    if not context.stop_requested:
        actions.pyautogui_module().hotkey('command' if sys.platform == 'darwin' else 'ctrl', 'v')
    return text

class LocalOcrExecutor(InstructionExecutorBase):

    def execute_once(self, context, command):
        if command.type_id != self.TYPE_ID:
            raise ValueError('OCR指令类型不匹配')
        (delegated, result) = actions.delegated(context, self.TYPE_ID, command)
        if delegated:
            return result
        parameters = validate(self.TYPE_ID, command.parameters)
        if not actions.wait_interruptibly(context, 0):
            return None
        if self.TYPE_ID == 'OCR点击识别区域' and parameters['点击来源'] == '前序OCR变量':
            name = parameters['变量']
            value = context.variables.get(name)
            details = context.variables.get(name + '_详情')
            if name == '最近OCR结果':
                recent = context.metadata.get('last_ocr_result') or {}
                (value, details) = (recent.get('value'), recent.get('matches'))
            index = parameters['第几个'] - 1
            if isinstance(details, list) and details:
                if index >= len(details):
                    raise ValueError('OCR变量中没有指定序号的识别结果')
                value = details[index].get('center')
            elif index != 0:
                raise ValueError('坐标变量只有一个结果，请选择第1个')
            if not isinstance(value, (list, tuple)) or len(value) != 2:
                raise ValueError(f'变量“{name}”没有OCR坐标，请先执行识别指令并选择其结果变量')
            (x, y) = map(float, value)
            if not all((math.isfinite(v) for v in (x, y))):
                raise ValueError('OCR坐标不是有效数值')
            (dx, dy) = actions.point(parameters['点击位置'])
            if actions.wait_interruptibly(context, 0):
                actions.mouse_action(parameters['动作'], x + dx, y + dy)
                context.emit(f'OCR点击：读取变量 {name}，位置 {[x, y]}')
                return [x, y]
            return None
        if self.TYPE_ID == 'OCR粘贴':
            pyperclip = _module_imports.load('pyperclip')
            text = pyperclip.paste() if parameters['内容来源'] == '剪贴板' else context.metadata.get('last_ocr_text')
            if actions.wait_interruptibly(context, parameters['粘贴前等待']):
                return paste_text(context, text)
            return None
        context.metadata.pop('last_ocr_result', None)
        if self.TYPE_ID in TEXT_TYPES:
            context.metadata['last_ocr_text'] = None
        region = actions.region(parameters['区域'])
        offset = region[:2] if region else (0, 0)
        target = actions.substitute_variables(context, parameters.get('目标文字', ''))
        mode = '精准' if self.TYPE_ID == 'OCR精准找字点击' else parameters.get('匹配方式', '包含')
        waiting = self.TYPE_ID.startswith('OCR等待')
        remaining = parameters.get('等待超时', 0)
        consecutive = 0
        TEMP_FOLDER = _module_imports.load('TEMP_FOLDER')
        Path(TEMP_FOLDER).mkdir(parents=True, exist_ok=True)
        try:
            with TemporaryDirectory(prefix='ocr-', dir=TEMP_FOLDER) as directory, OcrSession() as session:
                while True:
                    if not actions.wait_interruptibly(context, 0):
                        return None
                    started = time.monotonic()
                    service = context.service('本地OCR')
                    if service:
                        rows = service(region=region, engine=parameters['引擎'], parameters=parameters)
                    else:
                        source = parameters.get('图像路径', '')
                        if source:
                            source = actions.substitute_variables(context, source)
                            source = actions.resolve_image_path({'图像路径': source}, context)
                            if not Path(source).is_file():
                                raise ValueError('OCR图片不存在：' + str(source))
                        else:
                            source = str(Path(directory) / 'capture.png')
                            actions.pyautogui_module().screenshot(region=region).save(source)
                        timeout = min(parameters['识别超时'], remaining) if waiting else parameters['识别超时']
                        pool = getattr(getattr(context, 'runtime', None), 'ocr_pool', None)
                        rows = (pool or session).recognize(source, parameters['引擎'], parameters, context, timeout)
                    if context.stop_requested:
                        return None
                    rows = validated_rows(rows, offset, parameters['置信度'])
                    if self.TYPE_ID in TEXT_TYPES:
                        if not actions.wait_interruptibly(context, 0):
                            return None
                        if not rows and parameters['未找到'] == '报错':
                            raise ValueError('OCR未识别到文字')
                        value = '\n'.join((row['text'] for row in rows))
                        context.metadata['last_ocr_result'] = {'value': value, 'matches': rows}
                        context.metadata['last_ocr_text'] = value
                        after = parameters.get('识别后', '仅保存最近OCR结果')
                        if after == '复制到剪贴板':
                            pyperclip = _module_imports.load('pyperclip')
                            pyperclip.copy(value)
                        elif after == '复制并粘贴':
                            paste_text(context, value)
                        context.emit(f'本地OCR：提取 {len(rows)} 个文字框')
                        return _write_result(context, parameters, value, rows) if '变量' in parameters else value
                    matches = rows if self.TYPE_ID in REGION_TYPES and (not target.strip()) else find_matches(rows, target, mode, parameters['相似度'], parameters['忽略大小写'], parameters['忽略空白'])
                    matches = order_matches(matches, parameters, region)
                    selected = matches[parameters['第几个'] - 1] if len(matches) >= parameters['第几个'] else None
                    if waiting:
                        satisfied = not matches if self.TYPE_ID == 'OCR等待文字消失' else selected is not None
                        consecutive = consecutive + 1 if satisfied else 0
                        remaining -= time.monotonic() - started
                        if consecutive < parameters['连续次数']:
                            if remaining <= 0:
                                raise TimeoutError('等待OCR文字条件超时')
                            delay = min(parameters['检测间隔'], remaining)
                            if not actions.wait_interruptibly(context, delay):
                                return None
                            remaining -= delay
                            if remaining <= 0:
                                raise TimeoutError('等待OCR文字条件超时')
                            continue
                    if not actions.wait_interruptibly(context, 0):
                        return None
                    if self.TYPE_ID == 'OCR等待文字消失':
                        return _write_result(context, parameters, True, [])
                    if selected is None:
                        _write_result(context, parameters, None, [])
                        if parameters.get('未找到', '报错') == '报错':
                            raise ValueError('OCR未找到指定文字或匹配序号超出范围')
                        return None
                    value = selected['center']
                    if self.TYPE_ID in ('OCR精准找字点击', 'OCR点击识别区域') or (self.TYPE_ID == 'OCR范围找字' and parameters['找到后'] == '点击区域'):
                        (x, y) = actions.point(parameters['点击位置'])
                        actions.mouse_action(parameters['动作'], value[0] + x, value[1] + y)
                    context.emit(f'{self.TYPE_ID}：匹配 {len(matches)} 项，位置 {value}')
                    return _write_result(context, parameters, value, matches)
        except OcrCancelled:
            return None
