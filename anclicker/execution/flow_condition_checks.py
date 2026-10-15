"""Read-only visual predicates used by condition and conditional-loop nodes."""
import math
import re
from pathlib import Path
from anclicker.platform.image_paths import resolve_image_reference
from anclicker.instructions.common import actions

from anclicker._imports import DeferredImports as _DeferredImports

# Dependencies declared here retain their existing on-demand loading boundaries.
_module_imports = _DeferredImports(globals(), {
    'rgb': ('from', 'anclicker.instructions.键鼠.颜色判断.executor', ('rgb',), 0),
    '_condition_value': ('from', 'anclicker.domain.expressions', ('_condition_value',), 0),
    'best_image_match': ('from', 'anclicker.execution.instruction_helpers.image_match', ('best_image_match',), 0),
    'LocalOcrExecutor': ('from', 'anclicker.instructions.common.local_ocr_instruction', ('LocalOcrExecutor',), 0),
    'CommandRecord_ExecutionContext': ('from', 'anclicker.domain.instructions', ('CommandRecord', 'ExecutionContext'), 0),
})


KINDS = ('表达式', '图片存在', '图片文件存在', 'OCR文字存在', '颜色判断', '坐标存在')
KIND_ALIASES = {'文字存在': 'OCR文字存在', '屏幕图片存在': '图片存在'}


def condition_kind(parameters):
    kind = parameters.get('判断类型', '表达式')
    return KIND_ALIASES.get(kind, kind)


def has_variable(value):
    return bool(re.search(r'\{\{[^{}]+\}\}|☾[^☽]+☽', str(value)))


def substitute_target(context, value):
    def replace(match):
        name = (match.group(1) or match.group(2)).strip()
        if name not in context.variables:
            raise KeyError('判断变量不存在：' + name)
        result = context.variables[name]
        return '' if result is None else str(result)
    return re.sub(r'\{\{([^{}]+)\}\}|☾([^☽]+)☽', replace, value)


def image_file_path(value, context):
    # File predicates never substitute an unrelated image with the same basename.
    project = context.metadata.get('project_path')
    if not project:
        getter = getattr(context.metadata.get('database'), 'get_setting_value', None)
        project = getter('当前文件路径') if callable(getter) else None
    return Path(resolve_image_reference(value, project_path=project, legacy_search=False))


def validate_parameters(parameters):
    kind = condition_kind(parameters)
    if kind not in KINDS:
        raise ValueError('请选择有效的判断类型')
    if kind == '表达式':
        return
    required = {'图片文件存在': ('图像路径',), '图片存在': ('图像路径',), '颜色判断': ('坐标', '颜色'),
                'OCR文字存在': ('目标文字',), '坐标存在': ('坐标',)}[kind]
    for key in required:
        if not str(parameters.get(key, '')).strip():
            raise ValueError(key + '不能为空')
    if kind in ('图片存在', 'OCR文字存在') and not has_variable(parameters.get('区域', '')):
        region = actions.region(parameters.get('区域', ''))
        if region is not None and (region[2] <= 0 or region[3] <= 0):
            raise ValueError('识别区域宽高必须大于零')
    if kind in ('图片存在', 'OCR文字存在'):
        accuracy = float(parameters.get('精度', .8))
        if not math.isfinite(accuracy) or not 0 < accuracy <= 1:
            raise ValueError('识别精度必须在 0–1 之间')
    if kind == '颜色判断':
        rgb = _module_imports.load('rgb')
        if not has_variable(parameters['坐标']):
            actions.point(parameters['坐标'])
        if not has_variable(parameters['颜色']):
            rgb(parameters['颜色'])
        tolerance = float(parameters.get('容差', 0))
        if not tolerance.is_integer() or not 0 <= tolerance <= 255:
            raise ValueError('颜色容差必须为 0–255 的整数')
    if parameters.get('满足条件', '存在 / 相等') not in ('存在 / 相等', '不存在 / 不相等'):
        raise ValueError('请选择有效的判断方向')
    if kind == 'OCR文字存在' and parameters.get('匹配方式', '包含') not in ('精准', '包含', '模糊'):
        raise ValueError('请选择有效的文字匹配方式')

def evaluate(context, parameters):
    _condition_value = _module_imports.load('_condition_value')
    kind = condition_kind(parameters)
    if kind == '表达式':
        return _condition_value(str(parameters.get('条件', 'True')), context.variables)
    validate_parameters(parameters)
    if not actions.wait_interruptibly(context, 0):
        return False
    target_keys = {'图片存在': ('图像路径', '区域'), '图片文件存在': ('图像路径',),
                   'OCR文字存在': ('目标文字', '区域'), '颜色判断': ('坐标', '颜色'),
                   '坐标存在': ()}[kind]
    values = {k: substitute_target(context, v) if k in target_keys and isinstance(v, str) else v
              for k, v in parameters.items()}
    validate_parameters(values)
    if kind == '图片文件存在':
        result = image_file_path(values['图像路径'], context).is_file()
    elif kind == '图片存在':
        path = actions.resolve_image_path(values, context)
        if not Path(path).is_file():
            raise FileNotFoundError('判断图片不存在：' + path)
        best_image_match = _module_imports.load('best_image_match')
        result = best_image_match(path, actions.pyautogui_module().screenshot(),
            confidence=float(values.get('精度', .8)), grayscale=bool(values.get('灰度', False)),
            region=actions.region(values.get('区域', ''))) is not None
    elif kind == '颜色判断':
        rgb = _module_imports.load('rgb')
        target = rgb(values['颜色'])
        actual = rgb(actions.pyautogui_module().pixel(*actions.point(values['坐标'])))
        result = all(abs(a-b) <= int(values.get('容差', 0)) for a, b in zip(actual, target))
    elif kind == 'OCR文字存在':
        LocalOcrExecutor = _module_imports.load('LocalOcrExecutor')
        CommandRecord, ExecutionContext = _module_imports.load('CommandRecord_ExecutionContext')
        # Keep prior OCR output intact; this predicate only returns a boolean.
        probe = ExecutionContext(variables=dict(context.variables), services=context.services,
            output=context.output, metadata=context.metadata.copy(), runtime=context.runtime)
        class StopProxy:
            @property
            def stop_requested(self):
                return context.stop_requested
            def __getattr__(self, name):
                return getattr(probe, name)
        executor = LocalOcrExecutor()
        executor.TYPE_ID = 'OCR模糊找字返回坐标'
        options = {'目标文字': values['目标文字'], '区域': values.get('区域', ''),
                   '匹配方式': values.get('匹配方式', '包含'), '相似度': float(values.get('精度', .8)),
                   '引擎': 'RapidOCR', '变量': '_condition_ocr', '未找到': '返回空值'}
        result = executor.execute_once(StopProxy(), CommandRecord(0, executor.TYPE_ID, options)) is not None
    else:
        coordinate = str(parameters['坐标']).strip()
        if coordinate.startswith('{{') and coordinate.endswith('}}'):
            coordinate = context.variables.get(coordinate[2:-2].strip())
        elif coordinate in context.variables:
            coordinate = context.variables[coordinate]
        try:
            if coordinate is None or coordinate == '' or isinstance(coordinate, bool):
                raise ValueError('empty coordinate')
            if isinstance(coordinate, (list, tuple)) and len(coordinate) != 2:
                raise ValueError('expected x/y pair')
            if isinstance(coordinate, dict) and not {'x', 'y'} <= coordinate.keys():
                raise ValueError('missing x/y')
            x, y = actions.point(coordinate)
            result = math.isfinite(x) and math.isfinite(y)
        except (ValueError, TypeError, OverflowError):
            result = False
    if context.stop_requested:
        return False
    # Image-existence branches always mean present -> yes, absent -> no,
    # including saved nodes carrying the old inverse-direction option.
    if kind == '图片存在':
        return bool(result)
    return not result if parameters.get('满足条件') == '不存在 / 不相等' else bool(result)


def condition_summary(parameters):
    kind = condition_kind(parameters)
    if kind == '表达式':
        return str(parameters.get('条件', 'True'))
    label = kind
    if kind != '图片存在' and parameters.get('满足条件') == '不存在 / 不相等':
        label = kind.replace('存在', '不存在').replace('颜色判断', '颜色不相等')
    target = parameters.get({'图片存在': '图像路径', '图片文件存在': '图像路径',
                             'OCR文字存在': '目标文字', '颜色判断': '坐标',
                             '坐标存在': '坐标'}.get(kind, ''), '')
    if kind in ('图片存在', '图片文件存在'):
        # Accept Windows and POSIX separators without changing the stored path.
        target = str(target).replace('\\', '/').rsplit('/', 1)[-1]
    return label + '：' + str(target)
