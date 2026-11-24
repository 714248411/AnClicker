"""Shared fixed/ranged mouse movement duration parsing."""
import math
import re


def duration_bounds(value):
    text = str(value).strip().replace('秒', '').strip()
    parts = re.split(r'\s*[-~～—–至]\s*', text)
    try:
        if len(parts) not in (1, 2):
            raise ValueError()
        values = [float(part) for part in parts]
        if any(not math.isfinite(v) or v < 0 or v > 3600 for v in values):
            raise ValueError()
        low, high = values[0], values[-1]
        if low > high:
            raise ValueError()
        return low, high
    except (ValueError, TypeError):
        raise ValueError('移动时间请输入 0–3600 秒的数值或范围，例如 1 或 0.5-1.5') from None
