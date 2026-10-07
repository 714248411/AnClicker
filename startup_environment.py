"""Prepare writable application storage before importing desktop libraries."""

import os
import sys
import tempfile
from pathlib import Path


def storage_install_folder(install):
    # Portable user data must live outside Velopack's replaceable current folder.
    if (install.name.casefold() == "current" and (install / "sq.version").is_file()
            and (install.parent / "Update.exe").is_file()):
        return install.parent
    return install


def prepare_environment():
    override = os.environ.get("ANCLICKER_DATA_DIR", "").strip()
    frozen = getattr(sys, "frozen", False)
    install = Path(sys.executable).parent if frozen else Path(__file__).resolve().parent
    if override:
        target = Path(override).expanduser().resolve()
    elif not frozen or sys.platform == "win32":
        target = storage_install_folder(install) / "data"
    elif sys.platform == "darwin":
        target = Path.home() / "Library" / "Application Support" / "AnClicker"
    else:
        target = Path(os.environ.get("XDG_DATA_HOME", Path.home() / ".local/share")) / "AnClicker"

    def initialize(folder):
        folder.mkdir(parents=True, exist_ok=True)
        with tempfile.TemporaryFile(dir=folder) as probe:
            probe.write(b"AnClicker")
        for name in ("images", "exports", "logs", "temp"):
            (folder / name).mkdir(exist_ok=True)

    try:
        initialize(target)
    except PermissionError:
        if override or not frozen or sys.platform != "win32":
            raise
        target = Path(os.environ.get("LOCALAPPDATA", Path.home() / "AppData/Local")) / "AnClicker"
        initialize(target)
    os.environ["ANCLICKER_DATA_DIR"] = str(target)
    return target


def record_startup_error(folder, error):
    import traceback
    path = folder / "logs" / "startup-error.log"
    path.write_text("".join(traceback.format_exception(error)), encoding="utf-8")
    return path
