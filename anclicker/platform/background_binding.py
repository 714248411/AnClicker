"""Binding presets shared by the form and the isolated runtime."""
import math

LEGACY_AUTO = '自动优先 DX1 → DX2'
AUTO = '自动尝试后台 1 → 4'
LABELS = {'DX1': '后台1（DX1）', 'DX2': '后台2（DX2）', 'GDI 兼容': '后台3（GDI）', 'GDI2 兼容': '后台4（GDI2）'}

def canonical_preset(value):
    return AUTO if value == LEGACY_AUTO else {v:k for k,v in LABELS.items()}.get(value,value)

def display_preset(value):
    value = canonical_preset(value)
    return LABELS.get(value,value)

CUSTOM = '自定义'
PRESETS = (AUTO, *LABELS.values(), CUSTOM)
MODE_KEYS = ('图像模式', '鼠标模式', '键盘模式')
PROFILES = {
    'DX1': ('dx', 'dx', 'dx'),
    'DX2': ('dx2', 'dx2', 'dx'),
    'GDI 兼容': ('gdi', 'windows', 'windows'),
    'GDI2 兼容': ('gdi2', 'windows', 'windows'),
}


def selected_preset(parameters):
    # Preserve explicit modes saved before presets existed.
    return canonical_preset(parameters.get('绑定方案')) or (CUSTOM if any(k in parameters for k in MODE_KEYS) else AUTO)


def binding_attempts(parameters):
    preset = selected_preset(parameters)
    if preset not in (AUTO, CUSTOM, *PROFILES):
        raise ValueError('请选择有效的绑定方案')
    mode = int(parameters.get('绑定模式', '0'))
    if mode not in (0, 2):
        raise ValueError('绑定方式仅支持 0 或 2')
    wait = float(parameters.get('绑定等待', 0))
    if not math.isfinite(wait) or not 0 <= wait <= 10:
        raise ValueError('绑定后等待必须在 0–10 秒之间')
    capture = capture_enabled(parameters)
    if preset == CUSTOM:
        display = str(parameters.get('图像模式', 'gdi')).lower()
        mouse = str(parameters.get('鼠标模式', 'windows')).lower()
        keyboard = str(parameters.get('键盘模式', 'windows')).lower()
        # The plugin calls DX1 "dx"; never pass the UI alias "dx1" to it.
        display, mouse, keyboard = ('dx' if value == 'dx1' else value for value in (display, mouse, keyboard))
        if display not in ('dx', 'dx2', 'dx3', 'gdi', 'gdi2') or mouse not in ('dx', 'dx2', 'windows', 'windows2', 'windows3') or keyboard not in ('dx', 'windows'):
            raise ValueError('请选择有效的图像、鼠标与键盘模式')
        return [(CUSTOM, display if capture else 'normal', mouse, keyboard, mode)], wait
    names = tuple(PROFILES) if preset == AUTO else (preset,)
    if preset == AUTO:
        from anclicker.platform.background_preferences import preferred_preset
        preferred = preferred_preset()
        names = tuple(sorted(names, key=lambda name: name != preferred))
    return [(name, PROFILES[name][0] if capture else 'normal', *PROFILES[name][1:], mode) for name in names], wait


def capture_enabled(parameters):
    value = parameters.get('启用截图', True)
    if not isinstance(value, bool):
        raise ValueError('启用截图必须为开启或关闭')
    return value
