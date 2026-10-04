import os
import sys
import unittest
from unittest import mock

import functions


class PlatformSupportTests(unittest.TestCase):
    def test_data_directory_can_be_overridden(self):
        with mock.patch.dict(os.environ, {"ANCLICKER_DATA_DIR": "~/custom-anclicker"}):
            expected_ = os.path.abspath(os.path.expanduser("~/custom-anclicker"))
            self.assertEqual(functions.get_platform_data_folder(), expected_)

    def test_macos_frozen_data_directory_is_user_writable(self):
        with mock.patch.object(sys, "platform", "darwin"), mock.patch.object(
            sys, "frozen", True, create=True
        ), mock.patch.dict(os.environ, {}, clear=False):
            with mock.patch.dict(os.environ, {"ANCLICKER_DATA_DIR": ""}):
                data_folder_ = functions.get_platform_data_folder()
        self.assertTrue(data_folder_.endswith(os.path.join("Application Support", "AnClicker")))

    def test_linux_frozen_data_directory_honors_xdg(self):
        with mock.patch.object(sys, "platform", "linux"), mock.patch.object(
            sys, "frozen", True, create=True
        ), mock.patch.dict(
            os.environ,
            {"ANCLICKER_DATA_DIR": "", "XDG_DATA_HOME": os.path.join("tmp", "xdg")},
        ):
            self.assertEqual(
                functions.get_platform_data_folder(),
                os.path.join("tmp", "xdg", "AnClicker"),
            )

    def test_null_hotkey_backend_is_safe_to_unregister(self):
        backend_ = functions.NullSystemHotkey()
        backend_.unregister(("f10",))
        self.assertFalse(functions.global_hotkeys_supported(backend_))
        self.assertFalse(functions.is_hotkey_valid(backend_, ["f10"]))


if __name__ == "__main__":
    unittest.main()
