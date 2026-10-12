"""屏幕多坐标点击：依次执行，支持取点追加和独立随机偏移。"""
import math
import random
import re

from qt_compat.QtWidgets import QDialog, QMessageBox
from instructions.common.multi_point_canvas import MultiPointCanvas
from instructions.common import FieldSpec, InstructionExecutorBase, SchemaInstructionEditor
from instructions.common import actions
from .多坐标点击_ui import Ui_InstructionEditor


def parse_points(value):
    if isinstance(value, (list, tuple)):
        parts = value
    else:
        parts = [part.strip() for part in re.split(r'[;；\r\n]+', str(value or '')) if part.strip()]
    if not parts:
        raise ValueError('请取点或填写坐标，例如 100,200; 300,400')
    try:
        return [actions.point(part) for part in parts]
    except (TypeError, ValueError, OverflowError) as error:
        raise ValueError('坐标格式应为 x,y；多个点用分号分隔') from error


class InstructionEditor(SchemaInstructionEditor):
    TYPE_ID = DISPLAY_NAME = '多坐标点击'
    UI_CLASS = Ui_InstructionEditor
    FIELDS = (
        FieldSpec('坐标列表', '点击坐标', 'text', '', required=True),
        FieldSpec('动作', '点击方式', 'choice', '左键单击', ('左键单击', '左键双击', '右键单击', '中键单击')),
        FieldSpec('间隔', '各点间隔（秒）', 'float', 1, minimum=0, maximum=3600),
        FieldSpec('随机偏移', '随机偏移', 'choice', '关闭', ('关闭', '启用')),
        FieldSpec('水平偏移', '水平随机范围', 'int', 0, minimum=0, maximum=1000),
        FieldSpec('垂直偏移', '垂直随机范围', 'int', 0, minimum=0, maximum=1000),
    )

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self._controls['坐标列表'].setMaxLength(2147483647)

    def _validate_parameters(self, parameters):
        super()._validate_parameters(parameters)
        value = str(parameters['坐标列表'])
        if not any(mark in value for mark in ('${', '{{', '☾')):
            parse_points(value)

    def _run_auxiliary(self, key):
        if key != '坐标列表':
            return super()._run_auxiliary(key)
        target = self._controls[key]
        try:
            points = parse_points(target.text()) if target.text().strip() else []
        except ValueError as error:
            QMessageBox.warning(self, '坐标无效', str(error))
            return
        windows = []
        for window in (self.window(), getattr(self, '_workspace_owner', None),
                       self.parentWidget().window() if self.parentWidget() else None):
            if window is not None and window not in [item[0] for item in windows] and window.isVisible():
                windows.append((window, window.windowOpacity()))
        canvas = None
        try:
            for window, opacity in windows: window.setWindowOpacity(0)
            canvas = MultiPointCanvas(points, self)
            if canvas.exec() == QDialog.Accepted:
                target.setText('; '.join(f'{x},{y}' for x, y in canvas.points))
                target.setCursorPosition(len(target.text()))
        finally:
            if canvas is not None: canvas.deleteLater()
            for window, opacity in windows: window.setWindowOpacity(opacity)



class InstructionExecutor(InstructionExecutorBase):
    TYPE_ID = '多坐标点击'

    def execute_once(self, context, command):
        delegated, result = actions.delegated(context, self.TYPE_ID, command)
        if delegated:
            return result
        p = command.parameters
        raw = p.get('坐标列表', '')
        if isinstance(raw, str):
            raw = actions.substitute_variables(context, raw)
        points = parse_points(raw)
        action = p.get('动作', '左键单击')
        if action not in ('左键单击', '左键双击', '右键单击', '中键单击'):
            raise ValueError('请选择有效的点击方式')
        gap = float(p.get('间隔', 1))
        if not math.isfinite(gap) or not 0 <= gap <= 3600:
            raise ValueError('各点间隔应在 0～3600 秒之间')
        enabled = p.get('随机偏移', '关闭') == '启用'
        rx, ry = int(p.get('水平偏移', 0)), int(p.get('垂直偏移', 0))
        if not 0 <= rx <= 1000 or not 0 <= ry <= 1000:
            raise ValueError('随机偏移范围应在 0～1000 像素之间')
        clicked = []
        for index, (x, y) in enumerate(points):
            if not actions.wait_interruptibly(context, 0):
                break
            if enabled:
                x += random.randint(-rx, rx)
                y += random.randint(-ry, ry)
            actions.mouse_action(action, x, y, interval_=0.1)
            clicked.append((x, y))
            context.emit(f'多坐标点击：第 {index + 1}/{len(points)} 点，{x},{y}')
            if index + 1 < len(points) and not actions.wait_interruptibly(context, gap):
                break
        return clicked
