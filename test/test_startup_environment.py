import os
from pathlib import Path
import tempfile
from unittest import mock

from startup_environment import prepare_environment


def test_first_launch_creates_storage_and_preserves_existing_files():
    with tempfile.TemporaryDirectory() as folder:
        target = Path(folder) / "new-install"
        with mock.patch.dict(os.environ, {"ANCLICKER_DATA_DIR": str(target)}):
            assert prepare_environment() == target
            for name in ("images", "exports", "logs", "temp"):
                assert (target / name).is_dir()
            sentinel = target / "images" / "saved.png"
            sentinel.write_bytes(b"existing-user-file")
            assert prepare_environment() == target
            assert sentinel.read_bytes() == b"existing-user-file"


def test_windows_read_only_install_uses_local_app_data():
    with tempfile.TemporaryDirectory() as folder:
        executable = Path(folder) / "protected" / "AnClicker.exe"
        fallback = Path(folder) / "local" / "AnClicker"
        original_mkdir = Path.mkdir

        def mkdir(path, *args, **kwargs):
            if path == executable.parent / "data":
                raise PermissionError("read-only installation")
            return original_mkdir(path, *args, **kwargs)

        with mock.patch.dict(os.environ, {"ANCLICKER_DATA_DIR": "", "LOCALAPPDATA": str(fallback.parent)}), \
             mock.patch("sys.frozen", True, create=True), \
             mock.patch("sys.platform", "win32"), \
             mock.patch("sys.executable", str(executable)), \
             mock.patch.object(Path, "mkdir", mkdir):
            assert prepare_environment() == fallback
            assert (fallback / "logs").is_dir()
