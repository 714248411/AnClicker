"""Native fallbacks for recorded inputs; importing this module installs no hooks."""
import sys


def keyboard_controller(context):
    from pynput import keyboard
    if "recording_keyboard_controller" not in context.metadata:
        context.metadata["recording_keyboard_controller"] = keyboard.Controller()
    return keyboard, context.metadata["recording_keyboard_controller"]


def mouse_controller(context):
    from pynput import mouse
    if "recording_mouse_controller" not in context.metadata:
        context.metadata["recording_mouse_controller"] = mouse.Controller()
    return mouse, context.metadata["recording_mouse_controller"]


def windows_key_parameters(token, down):
    _, vk, scan, extended = token.split(":")
    vk, scan, extended = int(vk), int(scan), int(extended)
    if not (0 <= vk <= 255 and 0 <= scan <= 65535 and extended in (0, 1)):
        raise ValueError("录制按键码无效")
    flags = 0 if down else 2  # KEYEVENTF_KEYUP
    if vk == 0xE7:  # VK_PACKET: UTF-16 input, not a physical scan code.
        return dict(wVk=0, wScan=scan, dwFlags=flags | 4)
    if scan and vk != 0x13:  # Pause has a special multi-byte scan sequence.
        return dict(wVk=0, wScan=scan, dwFlags=flags | extended | 8)
    return dict(wVk=vk, wScan=scan, dwFlags=flags | extended)


def send_windows_key(token, down):
    if sys.platform != "win32":
        raise RuntimeError("此按键以 Windows 原始键码录制，请在 Windows 回放")
    import ctypes
    from pynput._util.win32 import INPUT, INPUT_union, KEYBDINPUT, SendInput
    event = INPUT(type=INPUT.KEYBOARD, value=INPUT_union(
        ki=KEYBDINPUT(**windows_key_parameters(token, down))))
    if SendInput(1, ctypes.byref(event), ctypes.sizeof(INPUT)) != 1:
        raise RuntimeError("系统拒绝模拟按键；请检查目标程序与本软件的权限级别")


def key_event(context, key, down, gui):
    if key.startswith("win32:"):
        send_windows_key(key, down)
        return
    if key.startswith(("special:", "native:", "char:")):
        keyboard, controller = keyboard_controller(context)
        if key.startswith("special:"):
            value = getattr(keyboard.Key, key.split(":", 1)[1], None)
            if value is None:
                raise ValueError(f"当前系统不支持录制按键：{key}")
        elif key.startswith("native:"):
            _, platform, vk = key.split(":")
            if platform != sys.platform:
                raise ValueError(f"此按键需在 {platform} 系统回放")
            value = keyboard.KeyCode.from_vk(int(vk))
        else:
            value = keyboard.KeyCode.from_char(key.split(":", 1)[1])
        (controller.press if down else controller.release)(value)
    else:
        (gui.keyDown if down else gui.keyUp)(key, _pause=False)


def button_event(context, button, down, gui):
    if button in {"left", "right", "middle"}:
        (gui.mouseDown if down else gui.mouseUp)(button=button, _pause=False)
    else:
        mouse, controller = mouse_controller(context)
        value = getattr(mouse.Button, button, None)
        if value is None or button == "unknown":
            raise ValueError(f"当前系统不支持鼠标按键：{button}")
        (controller.press if down else controller.release)(value)


def scroll_event(context, dx, dy):
    _, controller = mouse_controller(context)
    controller.scroll(dx, dy)
