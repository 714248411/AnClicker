"""Lazy mouse trajectories; no input injection or button ownership here.

Human curve design adapted from HumanCursor's random knots / Bezier / tween
pipeline (MIT, Flori Batusha). See HumanCursor-LICENSE.txt. This implementation
uses a bounded cubic curve and minimum-jerk timing rather than upstream's
independent point noise; it needs neither numpy nor scipy.
"""
import math
import random

TRAJECTORIES = ("直线", "模拟人类曲线（贝塞尔）")


def trajectory(start, end, steps, mode="直线", rng=None, bounds=None):
    """Yield steps points excluding start, including the exact end, in O(1) space."""
    if mode not in TRAJECTORIES:
        raise ValueError(f"未知鼠标移动轨迹：{mode}")
    if not isinstance(steps, int) or steps < 1:
        raise ValueError("移动步数必须为正整数")
    rng = rng or random
    dx, dy = end[0] - start[0], end[1] - start[1]
    distance = math.hypot(dx, dy)
    # A small perpendicular bend also works for horizontal/vertical drags.
    # Optional screen bounds clamp control points, hence the entire curve.
    if mode != "直线" and distance:
        a, b = rng.uniform(.18, .38), rng.uniform(.62, .82)
        bend = rng.choice((-1, 1)) * min(40, distance * rng.uniform(.08, .18))
        ox, oy = -dy / distance * bend, dx / distance * bend
        c1 = (start[0] + dx * a + ox, start[1] + dy * a + oy)
        c2 = (start[0] + dx * b + ox, start[1] + dy * b + oy)
        if bounds is not None:
            left, top, right, bottom = bounds
            c1 = (min(right, max(left, c1[0])), min(bottom, max(top, c1[1])))
            c2 = (min(right, max(left, c2[0])), min(bottom, max(top, c2[1])))
    for step in range(1, steps + 1):
        if step == steps:
            yield tuple(end)
            continue
        t = step / steps
        if mode == "直线" or not distance:
            x, y = start[0] + dx * t, start[1] + dy * t
        else:
            t = t * t * t * (10 + t * (-15 + 6 * t))
            u = 1 - t
            x = u**3 * start[0] + 3*u*u*t*c1[0] + 3*u*t*t*c2[0] + t**3*end[0]
            y = u**3 * start[1] + 3*u*u*t*c1[1] + 3*u*t*t*c2[1] + t**3*end[1]
        yield round(x), round(y)


def screen_bounds(gui, start, end):
    """Use physical virtual-desktop bounds on Windows, primary bounds elsewhere.

    Never force negative/multi-monitor coordinates onto the primary screen.
    Unknown layouts remain protected by the input backend's fail-safe.
    """
    import sys
    try:
        if sys.platform == "win32":
            import ctypes
            metrics = ctypes.windll.user32.GetSystemMetrics
            x, y, w, h = (metrics(i) for i in (76, 77, 78, 79))
        else:
            w, h = gui.size()
            x = y = 0
        if w > 0 and h > 0 and all(x <= p[0] < x+w and y <= p[1] < y+h for p in (start, end)):
            return x, y, x+w-1, y+h-1
    except (AttributeError, TypeError, OSError, ValueError):
        pass
    return None


def wait_interruptibly(context, seconds):
    from instructions.common import actions
    steps = max(1, math.ceil(seconds / .02))
    for _ in range(steps):
        if context.stop_requested:
            return False
        if seconds:
            actions.wait_seconds(seconds / steps)
    return not context.stop_requested
