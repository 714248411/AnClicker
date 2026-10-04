import os
import tempfile
import unittest

from PySide6.QtGui import QImage

from functions import RESOURCE_FOLDER
from info import CURRENT_VERSION, QQ, QQ_GROUP
from 数据库操作 import DatabaseOperation


class BrandingAndThemeTests(unittest.TestCase):
    def test_branding_and_qq_group_are_current(self):
        self.assertEqual(CURRENT_VERSION, "v1.0.0 Beat")
        self.assertEqual(QQ, "84284936")
        self.assertIn("group_code=84284936", QQ_GROUP)
        self.assertTrue(QQ_GROUP.startswith("http://qm.qq.com/cgi-bin/qm/qr?"))

    def test_light_theme_is_default_but_later_choice_is_preserved(self):
        with tempfile.TemporaryDirectory() as directory:
            db_path = os.path.join(directory, "settings.db")
            database = DatabaseOperation(db_path)
            self.assertEqual(database.get_setting_value("界面主题"), "light")
            database.set_setting_value("界面主题", "dark")

            reopened = DatabaseOperation(db_path)
            self.assertEqual(reopened.get_setting_value("界面主题"), "dark")

    def test_donation_qr_is_bundled_and_readable(self):
        image_path = os.path.join(RESOURCE_FOLDER, "Window", "res", "donation_qr.png")
        self.assertTrue(os.path.isfile(image_path))
        self.assertFalse(QImage(image_path).isNull())


if __name__ == "__main__":
    unittest.main()
