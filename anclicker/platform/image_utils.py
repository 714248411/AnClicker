"""Image names and Unicode OpenCV compatibility."""
import os
import re

from anclicker._imports import DeferredImports as _DeferredImports

# Dependencies declared here retain their existing on-demand loading boundaries.
_module_imports = _DeferredImports(globals(), {
    'cv2': ('import', 'cv2', (), False),
    'np': ('import', 'numpy', (), True),
    'pyscreeze': ('import', 'pyscreeze', (), False),
})


_INVALID_WINDOWS_FILENAME_CHARS = re.compile(r'[<>:"/\\|?*\x00-\x1f]')
_WINDOWS_RESERVED_NAMES = {
    "CON", "PRN", "AUX", "NUL",
    *(f"COM{index}" for index in range(1, 10)),
    *(f"LPT{index}" for index in range(1, 10)),
}


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
    cv2 = _module_imports.load('cv2')
    np = _module_imports.load('np')
    pyscreeze = _module_imports.load('pyscreeze')

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
