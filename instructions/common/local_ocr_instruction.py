"""Shared schema/runtime for the individually draggable offline OCR commands."""
from pathlib import Path
from tempfile import TemporaryDirectory
import math
import time

from . import FieldSpec, SchemaInstructionEditor, InstructionExecutorBase, actions
from local_ocr import OcrSession, OcrCancelled, validated_rows, find_matches

OCR_TYPES = ('OCR文字提取', 'OCR精准找字点击', 'OCR模糊找字返回坐标',
             'OCR范围找字', 'OCR等待文字出现', 'OCR等待文字消失',
             '截图OCR', 'OCR复制', 'OCR粘贴', 'OCR识别区域返回坐标', 'OCR点击识别区域')
TEXT_TYPES = ('OCR文字提取', '截图OCR', 'OCR复制')
REGION_TYPES = ('OCR识别区域返回坐标', 'OCR点击识别区域')
CLICK_TYPES = ('OCR精准找字点击', 'OCR点击识别区域', 'OCR范围找字')


def fields_for(name):
    if name == 'OCR粘贴':
        return (FieldSpec('内容来源', '粘贴内容来源（无需变量）', 'choice', '最近OCR结果', ('最近OCR结果', '剪贴板')),
                FieldSpec('粘贴前等待', '粘贴前等待（秒）', 'float', .3, minimum=0, maximum=60))
    fields = [FieldSpec('引擎', '离线引擎', 'choice', 'RapidOCR', ('RapidOCR', '微信OCR')),
              FieldSpec('区域', '识别区域 x,y,w,h（空为全屏）', 'text', '', required=name in ('OCR范围找字', '截图OCR', 'OCR复制'))]
    if name in TEXT_TYPES:
        if name != 'OCR文字提取':
            fields.append(FieldSpec('识别后', '识别后操作（无需变量）', 'choice', '复制到剪贴板',
                                    ('仅保存最近OCR结果', '复制到剪贴板', '复制并粘贴')))
    if name == 'OCR文字提取':
        fields.append(FieldSpec('图像路径', '图片文件（空为屏幕截图）'))
    elif name not in TEXT_TYPES:
        fields.append(FieldSpec('目标文字', '目标文字（区域模块可留空匹配全部文字框）', required=name not in REGION_TYPES))
        if name != 'OCR精准找字点击':
            fields.append(FieldSpec('匹配方式', '文字匹配方式', 'choice',
                '模糊' if name == 'OCR模糊找字返回坐标' else '包含', ('精准', '包含', '模糊')))
        fields += [FieldSpec('相似度', '模糊相似度 0–1', 'float', .8, minimum=.01, maximum=1),
                   FieldSpec('第几个', '排序后的第几个区域（从1开始）', 'int', 1, minimum=1, maximum=10000),
                   FieldSpec('排序方式', '匹配区域排序', 'choice', '从上到下', ('从上到下', '离锚点最近')),
                   FieldSpec('中心锚点', '屏幕锚点 x,y（空为识别范围中心）', 'text', ''),
                   FieldSpec('忽略大小写', '忽略英文大小写', 'bool', True),
                   FieldSpec('忽略空白', '忽略空白字符', 'bool', True)]
    fields.append(FieldSpec('置信度', '最低识别置信度 0–1', 'float', .5, minimum=0, maximum=1))
    if name not in ('截图OCR', 'OCR复制'):
        fields.append(FieldSpec('变量', '结果变量（可自定义）', 'text', 'OCR文字' if name == 'OCR文字提取' else 'OCR坐标', required=True))
    if name == 'OCR范围找字':
        fields.append(FieldSpec('找到后', '找到后的操作', 'choice', '返回坐标', ('返回坐标', '点击区域')))
    if name in CLICK_TYPES:
        fields += [FieldSpec('动作', '点击动作', 'choice', '左键单击', ('左键单击', '左键双击', '右键单击')),
                   FieldSpec('点击位置', '相对文字框中心偏移 x,y', 'text', '(0,0)')]
    if name.startswith('OCR等待'):
        fields += [FieldSpec('等待超时', '等待超时（秒，不含暂停）', 'float', 30, minimum=.1, maximum=86400),
                   FieldSpec('检测间隔', '检测间隔（秒）', 'float', .5, minimum=.1, maximum=60),
                   FieldSpec('连续次数', '连续满足次数（降低误判）', 'int', 2, minimum=1, maximum=100)]
    else:
        fields.append(FieldSpec('未找到', '未找到文字时', 'choice', '报错', ('报错', '返回空值')))
    fields += [FieldSpec('识别超时', '单次识别超时（秒，含引擎启动）', 'float', 30, minimum=1, maximum=300),
               FieldSpec('微信OCR路径', '微信OCR文件（exe / dll / wxocr）'),
               FieldSpec('微信运行目录', '微信安装版本目录'),
               FieldSpec('微信接口目录', 'wcocr接口目录（可选）')]
    return tuple(fields)


def validate(name, parameters):
    defaults = {f.key: f.default for f in fields_for(name)}
    defaults.update(parameters)
    for field in fields_for(name):
        value = defaults[field.key]
        if field.required and not str(value).strip():
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
        if not all(math.isfinite(float(v)) for v in anchor):
            raise ValueError('中心锚点必须是有限坐标')
    elif defaults.get('排序方式') == '离锚点最近' and not region:
        raise ValueError('就近识别请设置识别范围或屏幕中心锚点')
    return defaults


class LocalOcrEditor(SchemaInstructionEditor):
    def __init__(self, parent=None, draft=None, context=None):
        super().__init__(parent, draft=draft, context=context)
        if '引擎' in self._controls:
            self._controls['引擎'].currentTextChanged.connect(self._engine_changed)
            self._engine_changed(self._controls['引擎'].currentText())

    def _engine_changed(self, engine):
        for index, field in enumerate(self.FIELDS):
            if field.key.startswith('微信'):
                self._controls[field.key].setEnabled(engine == '微信OCR')
                self._controls[field.key].setToolTip('可留空自动查找本机常见路径；私有组件不会随包分发。')
                button = getattr(self.ui, f'auxiliary_{index}', None)
                if button is not None:
                    button.setEnabled(engine == '微信OCR')

    def _validate_parameters(self, parameters):
        super()._validate_parameters(parameters)
        validate(self.TYPE_ID, parameters)

    def _run_auxiliary(self, key):
        from PySide6.QtWidgets import QFileDialog
        if key == '区域':
            from PySide6.QtCore import QTimer
            from PySide6.QtWidgets import QDialog, QMessageBox
            from smart_capture import SmartCaptureDialog
            owner = self.parentWidget().window() if self.parentWidget() else None
            visible = owner is not None and owner.isVisible()
            self.hide()
            if visible:
                owner.hide()
            def choose():
                dialog = None
                try:
                    dialog = SmartCaptureDialog()
                    if dialog.exec() == QDialog.DialogCode.Accepted:
                        self._set_control_value(self._controls[key], str(dialog.selected_region()))
                except Exception as error:
                    QMessageBox.warning(self, '框选失败', str(error))
                finally:
                    if dialog is not None:
                        dialog.deleteLater()
                    if visible:
                        owner.show()
                    self.show()
                    self.activateWindow()
            QTimer.singleShot(180, choose)
        elif key == '微信OCR路径':
            path, _ = QFileDialog.getOpenFileName(self, '选择本机微信OCR文件')
            if path:
                self._set_control_value(self._controls[key], path)
        elif key in ('微信运行目录', '微信接口目录'):
            path = QFileDialog.getExistingDirectory(self, '选择目录')
            if path:
                self._set_control_value(self._controls[key], path)
        else:
            super()._run_auxiliary(key)


def _write_result(context, parameters, value, matches):
    name = parameters['变量']
    context.set_variable(name, value)
    context.set_variable(name + '_详情', matches)
    point = value if isinstance(value, list) and len(value) == 2 else None
    context.set_variable(name + '_X', point[0] if point else None)
    context.set_variable(name + '_Y', point[1] if point else None)
    context.set_variable(name + '_区域', matches[parameters.get('第几个', 1)-1]['box']
                         if point and len(matches) >= parameters.get('第几个', 1) else None)
    return value


def order_matches(matches, parameters, region):
    """Distance uses absolute screen coordinates, after crop offset is applied."""
    if parameters.get('排序方式') != '离锚点最近':
        return matches
    anchor = parameters.get('中心锚点', '').strip()
    x, y = actions.point(anchor) if anchor else (region[0] + region[2]/2, region[1] + region[3]/2)
    return sorted(matches, key=lambda row: (row['center'][0]-x)**2 + (row['center'][1]-y)**2)


def paste_text(context, text):
    if not isinstance(text, str) or not text:
        raise ValueError('没有可粘贴的OCR文字；请先识别/复制文字。')
    if not actions.wait_interruptibly(context, 0):
        return None
    import pyperclip
    import sys
    pyperclip.copy(text)
    if not context.stop_requested:
        actions.pyautogui_module().hotkey('command' if sys.platform == 'darwin' else 'ctrl', 'v')
    return text


class LocalOcrExecutor(InstructionExecutorBase):
    def execute_once(self, context, command):
        if command.type_id != self.TYPE_ID:
            raise ValueError('OCR指令类型不匹配')
        delegated, result = actions.delegated(context, self.TYPE_ID, command)
        if delegated:
            return result
        parameters = validate(self.TYPE_ID, command.parameters)
        if not actions.wait_interruptibly(context, 0):
            return None
        if self.TYPE_ID == 'OCR粘贴':
            import pyperclip
            text = (pyperclip.paste() if parameters['内容来源'] == '剪贴板'
                    else context.metadata.get('last_ocr_text'))
            if actions.wait_interruptibly(context, parameters['粘贴前等待']):
                return paste_text(context, text)
            return None
        if self.TYPE_ID in TEXT_TYPES:
            context.metadata['last_ocr_text'] = None
        region = actions.region(parameters['区域'])
        offset = region[:2] if region else (0, 0)
        target = actions.substitute_variables(context, parameters.get('目标文字', ''))
        mode = '精准' if self.TYPE_ID == 'OCR精准找字点击' else parameters.get('匹配方式', '包含')
        waiting = self.TYPE_ID.startswith('OCR等待')
        remaining = parameters.get('等待超时', 0)
        consecutive = 0
        from functions import TEMP_FOLDER
        Path(TEMP_FOLDER).mkdir(parents=True, exist_ok=True)
        try:
            with TemporaryDirectory(prefix='ocr-', dir=TEMP_FOLDER) as directory, OcrSession() as session:
                while True:
                    # A paused worker cannot click or publish stale results.
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
                        rows = session.recognize(source, parameters['引擎'], parameters, context, timeout)
                    if context.stop_requested:
                        return None
                    rows = validated_rows(rows, offset, parameters['置信度'])
                    if self.TYPE_ID in TEXT_TYPES:
                        if not actions.wait_interruptibly(context, 0):
                            return None
                        if not rows and parameters['未找到'] == '报错':
                            raise ValueError('OCR未识别到文字')
                        value = '\n'.join(row['text'] for row in rows)
                        context.metadata['last_ocr_text'] = value
                        after = parameters.get('识别后', '仅保存最近OCR结果')
                        if after == '复制到剪贴板':
                            import pyperclip
                            pyperclip.copy(value)
                        elif after == '复制并粘贴':
                            paste_text(context, value)
                        context.emit(f'本地OCR：提取 {len(rows)} 个文字框')
                        return _write_result(context, parameters, value, rows) if '变量' in parameters else value
                    matches = (rows if self.TYPE_ID in REGION_TYPES and not target.strip() else
                               find_matches(rows, target, mode, parameters['相似度'],
                                            parameters['忽略大小写'], parameters['忽略空白']))
                    matches = order_matches(matches, parameters, region)
                    selected = matches[parameters['第几个']-1] if len(matches) >= parameters['第几个'] else None
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
                    if self.TYPE_ID in ('OCR精准找字点击', 'OCR点击识别区域') or (
                            self.TYPE_ID == 'OCR范围找字' and parameters['找到后'] == '点击区域'):
                        x, y = actions.point(parameters['点击位置'])
                        actions.mouse_action(parameters['动作'], value[0]+x, value[1]+y)
                    context.emit(f'{self.TYPE_ID}：匹配 {len(matches)} 项，位置 {value}')
                    return _write_result(context, parameters, value, matches)
        except OcrCancelled:
            return None
