import datetime
import os
import re
import sys
import time
import typing

import cv2
import numpy as np
import pyscreeze
import win32con
import win32gui
from system_hotkey import SystemHotkey, user32


_INVALID_WINDOWS_FILENAME_CHARS = re.compile(r'[<>:"/\\|?*\x00-\x1f]')
_WINDOWS_RESERVED_NAMES = {
    "CON", "PRN", "AUX", "NUL",
    *(f"COM{index}" for index in range(1, 10)),
    *(f"LPT{index}" for index in range(1, 10)),
}


def timer(func):
    def func_wrapper(*args, **kwargs):
        time_start = time.time()
        result = func(*args, **kwargs)
        time_end = time.time()
        time_spend = time_end - time_start
        print("%s cost time: %.3f s" % (func.__name__, time_spend))
        return result

    return func_wrapper


def normalize_png_filename(file_name: str) -> str:
    """校验并规范化 PNG 文件名，允许中文及其他 Unicode 字符。"""
    normalized_name = file_name.strip()
    if not normalized_name:
        raise ValueError("图像名称不能为空！")
    if file_name.rstrip(" .") != file_name:
        raise ValueError("图像名称不能以空格或句点结尾！")
    if _INVALID_WINDOWS_FILENAME_CHARS.search(normalized_name):
        raise ValueError('图像名称不能包含 < > : " / \\ | ? * 等非法字符！')

    base_name = normalized_name[:-4] if normalized_name.lower().endswith(".png") else normalized_name
    if not base_name or base_name in {".", ".."}:
        raise ValueError("请输入有效的图像名称！")
    if base_name.split(".", 1)[0].upper() in _WINDOWS_RESERVED_NAMES:
        raise ValueError("该图像名称是 Windows 保留名称，请更换！")

    return f"{base_name}.png"


def patch_pyautogui_unicode_cv2() -> bool:
    """使 PyAutoGUI/PyScreeze 能够读取包含 Unicode 字符的图像路径。"""
    if getattr(pyscreeze, "_unicode_cv2_patched", False):
        return True

    original_load_cv2 = getattr(pyscreeze, "_load_cv2", None)
    if original_load_cv2 is None:
        return False

    def load_cv2_unicode(img, grayscale=None):
        if not isinstance(img, str):
            return original_load_cv2(img, grayscale)

        if grayscale is None:
            grayscale = pyscreeze.GRAYSCALE_DEFAULT
        flag = cv2.IMREAD_GRAYSCALE if grayscale else cv2.IMREAD_COLOR

        try:
            image_data = np.fromfile(os.path.normpath(img), dtype=np.uint8)
            image = cv2.imdecode(image_data, flag) if image_data.size > 0 else None
        except Exception:
            image = None

        if image is None:
            raise OSError(f"Failed to read image: {img}")
        return image

    pyscreeze._load_cv2 = load_cv2_unicode
    pyscreeze._unicode_cv2_patched = True
    return True


def get_str_now_time():
    """获取当前时间"""
    return datetime.datetime.now().strftime('%Y-%m-%d %H:%M:%S')


def get_install_folder() -> str:
    """获取程序安装目录，用户数据保存在此目录下。"""
    if getattr(sys, "frozen", False):
        return os.path.dirname(sys.executable)
    return os.path.dirname(os.path.abspath(__file__))


def get_resource_folder() -> str:
    """获取只读程序资源目录。"""
    if getattr(sys, "frozen", False):
        return getattr(sys, "_MEIPASS", os.path.dirname(sys.executable))
    return os.path.dirname(os.path.abspath(__file__))


INSTALL_FOLDER = get_install_folder()
RESOURCE_FOLDER = get_resource_folder()
DATA_FOLDER = os.path.join(INSTALL_FOLDER, "data")
DATABASE_PATH = os.path.join(DATA_FOLDER, "命令集.db")
IMAGES_FOLDER = os.path.join(DATA_FOLDER, "images")
EXPORTS_FOLDER = os.path.join(DATA_FOLDER, "exports")
LOGS_FOLDER = os.path.join(DATA_FOLDER, "logs")
TEMP_FOLDER = os.path.join(DATA_FOLDER, "temp")


def ensure_data_directories() -> None:
    """创建 Clicker 所有可写数据目录。"""
    for folder in (
        DATA_FOLDER,
        IMAGES_FOLDER,
        EXPORTS_FOLDER,
        LOGS_FOLDER,
        TEMP_FOLDER,
    ):
        os.makedirs(folder, exist_ok=True)


def line_number_increment(old_value, number=1):
    """行号递增
    :param old_value: 旧的单元格号
    :param number: 递增的数量"""
    # 提取字母部分和数字部分
    column_letters = re.findall(r"[a-zA-Z]+", old_value)[0]
    line_number = int(re.findall(r"\d+\.?\d*", old_value)[0])
    # 计算新的行号
    new_line_number = line_number + number
    # 组合字母部分和新的行号
    new_cell_position = (column_letters + str(new_line_number)).upper()
    new_cell_position = new_cell_position
    return new_cell_position


def is_hotkey_valid(hkobj: SystemHotkey, hk: typing.List[str]):
    """判断快捷键是否有效"""
    hk = hkobj.order_hotkey(hk)
    try:
        keycode, masks = hkobj.parse_hotkeylist(hk)
        reg_hk_res = user32.RegisterHotKey(None, 1, masks, keycode)
        if reg_hk_res:
            user32.UnregisterHotKey(None, reg_hk_res)
            return True
    except Exception as e:
        print("获取快捷键注册信息失败！", e)
    return False


def show_window(title):
    """将指定标题的窗口正常显示，主要用于主窗口显示"""

    def get_window_titles(hwnd, titles):
        titles[hwnd] = win32gui.GetWindowText(hwnd)

    try:
        hwnd_title = {}
        win32gui.EnumWindows(get_window_titles, hwnd_title)
        for h, t in hwnd_title.items():
            if t == title:
                win32gui.ShowWindow(h, win32con.SW_SHOWNORMAL)  # 正常显示窗口
                win32gui.SetForegroundWindow(h)
                break
    except Exception as e:
        print(f"显示窗口出现错误: {e}")
