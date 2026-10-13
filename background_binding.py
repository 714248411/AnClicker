"""Binding presets shared by the form and the isolated runtime."""
import math

AUTO = '自动优先 DX1 → DX2'
CUSTOM = '自定义'
PRESETS = (AUTO, 'DX1', 'DX2', 'GDI 兼容', 'GDI2 兼容', CUSTOM)
MODE_KEYS = ('图像模式', '鼠标模式', '键盘模式')
PROFILES = {
    'DX1': ('dx', 'dx', 'dx'),
    'DX2': ('dx2', 'dx2', 'dx'),
    'GDI 兼容': ('gdi', 'windows', 'windows'),
    'GDI2 兼容': ('gdi2', 'windows', 'windows'),
}


def selected_preset(parameters):
    # Preserve explicit modes saved before presets existed.
    return parameters.get('绑定方案') or (CUSTOM if any(k in parameters for k in MODE_KEYS) else AUTO)


def binding_attempts(parameters):
    preset = selected_preset(parameters)
    if preset not in PRESETS:
        raise ValueError('请选择有效的绑定方案')
    mode = int(parameters.get('绑定模式', '0'))
    if mode not in (0, 2):
        raise ValueError('绑定方式仅支持 0 或 2')
    wait = float(parameters.get('绑定等待', 1))
    if not math.isfinite(wait) or not 0 <= wait <= 10:
        raise ValueError('绑定后等待必须在 0–10 秒之间')
    if preset == CUSTOM:
        display = str(parameters.get('图像模式', 'gdi')).lower()
        mouse = str(parameters.get('鼠标模式', 'windows')).lower()
        keyboard = str(parameters.get('键盘模式', 'windows')).lower()
        # The plugin calls DX1 "dx"; never pass the UI alias "dx1" to it.
        display, mouse, keyboard = ('dx' if value == 'dx1' else value for value in (display, mouse, keyboard))
        if display not in ('dx', 'dx2', 'dx3', 'gdi', 'gdi2') or mouse not in ('dx', 'dx2', 'windows', 'windows2', 'windows3') or keyboard not in ('dx', 'windows'):
            raise ValueError('请选择有效的图像、鼠标与键盘模式')
        return [(CUSTOM, display, mouse, keyboard, mode)], wait
    names = ('DX1', 'DX2') if preset == AUTO else (preset,)
    return [(name, *PROFILES[name], mode) for name in names], wait
