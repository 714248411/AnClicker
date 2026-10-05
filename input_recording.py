"""Opt-in, bounded input capture and conversion to ordinary persisted commands."""
from __future__ import annotations

from dataclasses import dataclass
from threading import RLock
import time
import uuid
import sys

from instructions.models import InstructionDraft


@dataclass(frozen=True)
class InputEvent:
    time: float
    kind: str
    data: tuple


class RecordingBuffer:
    """Listener threads write here; Qt only reads snapshots on its own thread."""
    def __init__(self, limit=2000, move_interval=0.05, clock=time.monotonic):
        self.limit = limit
        self.move_interval = move_interval
        self.clock = clock
        self.lock = RLock()
        self.events = []
        self.active = False
        self.full = False

    def start(self):
        with self.lock:
            self.events = []
            self.full = False
            self.started = self.clock()
            self.last_move = -1.0
            self.last_position = None
            self.pending_move = None
            self.active = True

    def _push(self, event):
        if len(self.events) >= self.limit:
            self.full = True
            self.active = False
            return False
        self.events.append(event)
        return True

    def append(self, kind, *data):
        with self.lock:
            if not self.active:
                return
            elapsed = max(0.0, self.clock() - self.started)
            if kind == "move":
                if data == self.last_position:
                    return
                self.last_position = data
                if elapsed - self.last_move < self.move_interval:
                    self.pending_move = InputEvent(elapsed, kind, tuple(data))
                    return
                self.pending_move = None
                self.last_move, self.last_position = elapsed, data
            elif self.pending_move is not None:
                if not self._push(self.pending_move):
                    return
                self.pending_move = None
            self._push(InputEvent(elapsed, kind, tuple(data)))

    def stop(self):
        with self.lock:
            if self.active and self.pending_move is not None:
                self._push(self.pending_move)
                self.pending_move = None
            self.active = False
            return tuple(self.events)

    def snapshot(self):
        with self.lock:
            return tuple(self.events)


def events_to_drafts(events, preserve_timing=True):
    """Keep independent down/up events, including modifiers during mouse drag."""
    group = uuid.uuid4().hex
    drafts = []
    keys, buttons = set(), set()
    position = (0, 0)
    origin = events[0].time if events else 0

    def add(type_id, parameters, when):
        parameters = dict(parameters)
        parameters.update({"录制批次": group, "录制时间": round(max(0, when - origin), 6)
                           if preserve_timing else 0})
        drafts.append(InstructionDraft(type_id, parameters, note="键鼠录制"))

    for event in events:
        kind, data = event.kind, event.data
        if kind == "key":
            key, down = data
            if not down and key not in keys:
                continue
            if down:
                keys.add(key)
            else:
                keys.discard(key)
            add("按下键盘", {"按键": key, "录制动作": "按下" if down else "松开",
                          "按压时长": 0}, event.time)
        elif kind == "button":
            x, y, button, down = data
            position = (x, y)
            if not down and button not in buttons:
                continue
            if down:
                buttons.add(button)
            else:
                buttons.discard(button)
            add("鼠标点击", {"鼠标": {"left": "左键", "right": "右键", "middle": "中键"}[button],
                          "录制动作": "按下" if down else "松开", "录制坐标": f"{x},{y}",
                          "次数": 1, "间隔": 0, "按压": 0}, event.time)
        elif kind == "move":
            x, y = data
            if buttons:
                add("鼠标拖拽", {"开始位置": f"{position[0]},{position[1]}",
                              "结束位置": f"{x},{y}", "移动速度": 0,
                              "录制保持按下": True}, event.time)
            else:
                add("移动鼠标", {"类型": "指定坐标", "坐标": f"{x},{y}", "持续": 0}, event.time)
            position = (x, y)
        elif kind == "scroll":
            x, y, delta = data
            if delta:
                add("滚轮滑动", {"类型": "滚轮滑动", "方向": "向上" if delta > 0 else "向下",
                              "距离": abs(int(delta)), "录制坐标": f"{x},{y}"}, event.time)
    # F8 can stop while an input is held. Always balance recorded presses.
    last_time = events[-1].time if events else 0
    for key in sorted(keys):
        add("按下键盘", {"按键": key, "录制动作": "松开", "按压时长": 0}, last_time)
    for button in sorted(buttons):
        add("鼠标点击", {"鼠标": {"left": "左键", "right": "右键", "middle": "中键"}[button],
                      "录制动作": "松开", "次数": 1, "间隔": 0, "按压": 0}, last_time)
    return drafts


def normalize_key(key, platform=None):
    """Use physical Windows VKs so Shift+A/Shift+1 are not replayed twice."""
    name = getattr(key, "name", None)
    platform = platform or sys.platform
    aliases = {"alt_l": "altleft", "alt_r": "altright", "ctrl_l": "ctrlleft",
               "ctrl_r": "ctrlright", "shift_l": "shiftleft", "shift_r": "shiftright",
               "cmd": "win", "cmd_l": "winleft", "cmd_r": "winright",
               "caps_lock": "capslock", "page_up": "pageup", "page_down": "pagedown",
               "num_lock": "numlock", "scroll_lock": "scrolllock", "print_screen": "printscreen"}
    if name:
        if platform == "darwin" and name in {"cmd", "cmd_l", "cmd_r"}:
            return "command"
        return aliases.get(name, name)
    vk = getattr(key, "vk", None)
    if platform == "win32" and vk is not None and (0x30 <= vk <= 0x39 or 0x41 <= vk <= 0x5A):
        return chr(vk).lower()
    punctuation = {0xBA: ";", 0xBB: "=", 0xBC: ",", 0xBD: "-", 0xBE: ".",
                   0xBF: "/", 0xC0: "`", 0xDB: "[", 0xDC: "\\", 0xDD: "]", 0xDE: "'"}
    if platform == "win32" and vk in punctuation:
        return punctuation[vk]
    char = getattr(key, "char", None)
    if char and len(char) == 1 and 1 <= ord(char) <= 26:
        return chr(ord(char) + 96)
    shifted = dict(zip('!@#$%^&*()_+{}|:"<>?~', '1234567890-=[]\\;\',./`'))
    return shifted.get(char, char.lower()) if char else None


class GlobalInputRecorder:
    """Listeners exist only between an explicit Start and Stop."""
    def __init__(self, buffer, stopped, failed, exclude_mouse=lambda x, y: False,
                 exclude_keyboard=lambda: False):
        self.buffer = buffer
        self.stopped = stopped
        self.failed = failed
        self.exclude_mouse = exclude_mouse
        self.exclude_keyboard = exclude_keyboard
        self.listeners = []
        self.active = False

    def start(self):
        from pynput import keyboard, mouse
        from pyautogui import KEYBOARD_KEYS
        self.active = True
        supported = set(KEYBOARD_KEYS)

        def safe(callback):
            def wrapped(*args):
                if not self.active:
                    return False
                try:
                    callback(*args)
                except Exception as error:
                    self.buffer.stop()
                    self.failed(str(error))
                    return False
            return wrapped

        def key_event(key, down):
            name = normalize_key(key)
            if name == "f8":
                if down:
                    self.buffer.stop()
                    self.stopped()
                return
            if not self.exclude_keyboard():
                if name in supported:
                    self.buffer.append("key", name, down)
                elif down:
                    self.buffer.stop()
                    self.failed(f"暂不支持录制此按键：{name or key}，已保留此前操作")

        def click(x, y, button, down):
            if not self.exclude_mouse(x, y) and button.name in {"left", "right", "middle"}:
                self.buffer.append("button", int(x), int(y), button.name, down)

        def move(x, y):
            if not self.exclude_mouse(x, y):
                self.buffer.append("move", int(x), int(y))

        def scroll(x, y, dx, dy):
            if not self.exclude_mouse(x, y):
                if dx:
                    self.buffer.stop()
                    self.failed("暂不支持水平滚轮录制，已保留此前操作")
                elif dy:
                    self.buffer.append("scroll", int(x), int(y), int(dy))

        try:
            self.listeners = [keyboard.Listener(on_press=safe(lambda k: key_event(k, True)),
                                                on_release=safe(lambda k: key_event(k, False))),
                              mouse.Listener(on_click=safe(click), on_move=safe(move), on_scroll=safe(scroll))]
            for listener in self.listeners:
                listener.start()
        except Exception:
            self.stop()
            raise

    def stop(self):
        self.active = False
        self.buffer.stop()
        listeners, self.listeners = self.listeners, []
        for listener in listeners:
            try:
                listener.stop()
            except RuntimeError:
                pass
        for listener in listeners:
            try:
                listener.join(timeout=0.5)
            except Exception:
                pass
