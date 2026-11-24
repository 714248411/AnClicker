"""Bounded, independently implemented mouse paths.
WindMouse model: https://ben.land/post/2021/04/25/windmouse-human-mouse-movement/
Bezier approach: https://github.com/vincentbavitz/bezmouse
"""
import math
import random
from anclicker.execution.actions import wait_interruptibly


def mouse_path(start, end, algorithm, rng=None):
    rng = rng or random
    sx, sy = map(float, start)
    ex, ey = map(float, end)
    distance = math.hypot(ex-sx, ey-sy)
    if distance < 1:
        return [(round(ex), round(ey))]
    points = []
    if algorithm == 'wind':
        x, y, vx, vy, wx, wy = sx, sy, 0., 0., 0., 0.
        for _ in range(2000):
            dx, dy = ex-x, ey-y
            remaining = math.hypot(dx, dy)
            if remaining < 1: break
            noise = min(2.5, remaining / 12)
            wx = wx * .65 + rng.uniform(-noise, noise)
            wy = wy * .65 + rng.uniform(-noise, noise)
            vx = vx * .72 + dx / remaining * 3.5 + wx
            vy = vy * .72 + dy / remaining * 3.5 + wy
            speed = math.hypot(vx, vy)
            limit = min(12., max(1., remaining * .3))
            if speed > limit:
                vx, vy = vx * limit / speed, vy * limit / speed
            x, y = x+vx, y+vy
            point = (round(x), round(y))
            if not points or point != points[-1]: points.append(point)
    else:
        nx, ny = -(ey-sy)/distance, (ex-sx)/distance
        bend = min(140., distance * .25)
        b1, b2 = rng.uniform(-bend,bend), rng.uniform(-bend,bend)
        c1 = (sx+(ex-sx)*.3+nx*b1, sy+(ey-sy)*.3+ny*b1)
        c2 = (sx+(ex-sx)*.7+nx*b2, sy+(ey-sy)*.7+ny*b2)
        for index in range(1, min(1000,max(16,math.ceil(distance/4)))+1):
            fraction = index/min(1000,max(16,math.ceil(distance/4)))
            t = fraction*fraction*(3-2*fraction)
            u = 1-t
            points.append((round(u**3*sx+3*u*u*t*c1[0]+3*u*t*t*c2[0]+t**3*ex),
                           round(u**3*sy+3*u*u*t*c1[1]+3*u*t*t*c2[1]+t**3*ey)))
    points.append((round(ex),round(ey)))
    return points


def avoid_failsafe_target(gui, target):
    """Reserve fail-safe corners for manual interruption, without disabling it."""
    target = tuple(map(int, target))
    if not getattr(gui, 'FAILSAFE', True) or getattr(gui, 'is_background', False) is True:
        return target
    width, height = gui.size()
    corners = getattr(gui, 'FAILSAFE_POINTS', ((0, 0), (width-1, 0), (0, height-1), (width-1, height-1)))
    if target not in corners:
        return target
    x, y = target
    return (min(width-1, max(0, x + (1 if x == 0 else -1))),
            min(height-1, max(0, y + (1 if y == 0 else -1))))


def move_human(gui, context, target, duration, algorithm):
    width, height = gui.size()
    target = (max(0,min(width-1,int(target[0]))), max(0,min(height-1,int(target[1]))))
    target = avoid_failsafe_target(gui, target)
    points = mouse_path(gui.position(),target,algorithm)
    delay = max(0.,duration)/len(points)
    for x,y in points:
        if context.stop_requested or not wait_interruptibly(context,delay):
            return tuple(map(int,gui.position()))
        point = avoid_failsafe_target(gui, (max(0,min(width-1,x)),max(0,min(height-1,y))))
        gui.moveTo(*point,duration=0,_pause=False)
    return target
