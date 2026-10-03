import tempfile
import unittest
from pathlib import Path

from functions import normalize_png_filename, patch_pyautogui_unicode_cv2


class UnicodeFilenameTest(unittest.TestCase):
    def test_chinese_filename_is_allowed(self):
        self.assertEqual(normalize_png_filename("登录按钮"), "登录按钮.png")
        self.assertEqual(normalize_png_filename("登录 按钮.PNG"), "登录 按钮.png")

    def test_invalid_windows_filenames_are_rejected(self):
        invalid_names = ["", "按钮?.png", "子目录/按钮.png", "CON.png", "按钮. "]
        for file_name in invalid_names:
            with self.subTest(file_name=file_name):
                with self.assertRaises(ValueError):
                    normalize_png_filename(file_name)


class UnicodeOpenCvPathTest(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        try:
            import cv2
            import numpy as np
            import pyscreeze
        except ImportError as error:
            raise unittest.SkipTest(f"图像识别依赖未安装: {error}")
        cls.cv2 = cv2
        cls.np = np
        cls.pyscreeze = pyscreeze

    def test_unicode_path_color_grayscale_and_idempotence(self):
        self.assertTrue(patch_pyautogui_unicode_cv2())
        patched_loader = self.pyscreeze._load_cv2
        self.assertTrue(patch_pyautogui_unicode_cv2())
        self.assertIs(self.pyscreeze._load_cv2, patched_loader)

        with tempfile.TemporaryDirectory() as temp_folder:
            image_folder = Path(temp_folder) / "中文资源目录"
            image_folder.mkdir()
            image_path = image_folder / "登录按钮.png"
            source_image = self.np.zeros((12, 18, 3), dtype=self.np.uint8)
            encoded_ok, encoded_image = self.cv2.imencode(".png", source_image)
            self.assertTrue(encoded_ok)
            encoded_image.tofile(str(image_path))

            color_image = self.pyscreeze._load_cv2(str(image_path), False)
            grayscale_image = self.pyscreeze._load_cv2(str(image_path), True)
            self.assertEqual(color_image.shape, (12, 18, 3))
            self.assertEqual(grayscale_image.shape, (12, 18))

            array_image = self.pyscreeze._load_cv2(source_image, False)
            self.assertEqual(array_image.shape, source_image.shape)

    def test_missing_unicode_path_raises_os_error(self):
        self.assertTrue(patch_pyautogui_unicode_cv2())
        with self.assertRaises(OSError):
            self.pyscreeze._load_cv2("不存在的目录/不存在的图像.png", False)


if __name__ == "__main__":
    unittest.main()
