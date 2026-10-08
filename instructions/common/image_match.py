"""Stateless best-match selection for the current template and screen pixels."""
from typing import NamedTuple


class ImageMatch(NamedTuple):
    x: int
    y: int
    score: float
    image_path: str


def best_image_match(image_path, screen, *, confidence, grayscale=False, region=None):
    import cv2
    import numpy as np
    from PIL import Image

    # Read the file every time, including when it was overwritten under the same
    # name. Neither templates, frames, nor coordinates are shared across calls.
    with Image.open(image_path) as source:
        needle = np.asarray(source.convert('RGB'))
    haystack = np.asarray(screen.convert('RGB'))
    if grayscale:
        needle = cv2.cvtColor(needle, cv2.COLOR_RGB2GRAY)
        haystack = cv2.cvtColor(haystack, cv2.COLOR_RGB2GRAY)
    x, y = 0, 0
    if region is not None:
        left, top, width, height = region
        x, y = max(0, left), max(0, top)
        right, bottom = min(haystack.shape[1], left + width), min(haystack.shape[0], top + height)
        haystack = haystack[y:max(y, bottom), x:max(x, right)]
    height, width = needle.shape[:2]
    if haystack.shape[0] < height or haystack.shape[1] < width:
        raise ValueError('目标图片大于当前识别区域，请重新设置区域或截图')
    # Normalized correlation is identically 1 for a constant template, so it
    # cannot distinguish any target. Report this instead of clicking a corner.
    if np.max(np.std(needle.astype(np.float32), axis=(0, 1))) < 1e-6:
        raise ValueError('目标图片没有可区分的细节，请重新截取包含文字或边框的图像')
    scores = cv2.matchTemplate(haystack, needle, cv2.TM_CCOEFF_NORMED)
    _, score, _, location = cv2.minMaxLoc(scores)
    if not np.isfinite(score) or score < confidence:
        return None
    return ImageMatch(x + location[0] + width // 2, y + location[1] + height // 2,
                      float(score), str(image_path))
