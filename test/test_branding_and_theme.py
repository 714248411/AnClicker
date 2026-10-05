import os
import tempfile
import unittest

from PySide6.QtGui import QImage

from functions import RESOURCE_FOLDER
from info import (
    CONTRIBUTORS,
    APP_NAME,
    CURRENT_VERSION,
    EMAIL_CONTACTS,
    GITEE_WEBSITE_SECOND,
    GITHUB_WEBSITE_OLD,
    Github_WEBSITE,
    ISSUE_WEBSITE_2,
    MAIN_WEBSITE,
    QQ,
    QQ_CONTACTS,
    QQ_GROUP,
    QQ_GROUP_OLD,
    QQ_OLD,
    WINDOW_TITLE,
)
from 数据库操作 import DatabaseOperation


class BrandingAndThemeTests(unittest.TestCase):
    def test_branding_and_qq_group_are_current(self):
        self.assertEqual(APP_NAME, "An Clicker")
        self.assertEqual(CURRENT_VERSION, "v1.0.2")
        self.assertEqual(WINDOW_TITLE, "An Clicker    [v1.0.2]")
        self.assertEqual(QQ, "84284936")
        self.assertIn("group_code=84284936", QQ_GROUP)
        self.assertTrue(QQ_GROUP.startswith("http://qm.qq.com/cgi-bin/qm/qr?"))
        self.assertEqual(QQ_OLD, "308994839")
        self.assertEqual(QQ_GROUP_OLD, "https://qm.qq.com/q/3ih3PE16Mg")
        self.assertEqual(QQ_CONTACTS, ("714248411", "2309636438"))
        self.assertEqual(
            EMAIL_CONTACTS, ("714248411@qq.com", "federalsadler@sohu.com")
        )
        self.assertEqual(CONTRIBUTORS, ("YanYi", "FasterThanLight"))
        self.assertEqual(
            MAIN_WEBSITE, "https://gitee.com/fasterthanlight/automatic_clicker_2"
        )
        self.assertEqual(Github_WEBSITE, "https://github.com/714248411/AnClicker")
        self.assertEqual(GITEE_WEBSITE_SECOND, "https://gitee.com/YiZhiYanYi/AnClicker")
        self.assertEqual(
            ISSUE_WEBSITE_2, "https://gitee.com/YiZhiYanYi/AnClicker/issues"
        )
        self.assertEqual(
            GITHUB_WEBSITE_OLD,
            "https://github.com/FsterThanLight/automatic_clicker_2",
        )

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
