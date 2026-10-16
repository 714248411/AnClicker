"""Prepare writable application storage before importing desktop libraries."""

import os
import sys
import tempfile
from pathlib import Path
from info import APP_ID, DATA_DIR_ENV

from anclicker._imports import DeferredImports as _DeferredImports

# Dependencies declared here retain their existing on-demand loading boundaries.
_module_imports = _DeferredImports(globals(), {
    'get_install_folder': ('from', 'anclicker.app.paths', ('get_install_folder',), 0),
    'traceback': ('import', 'traceback', (), False),
})



def storage_install_folder(install):
    # Portable user data must live outside Velopack's replaceable current folder.
    if (install.name.casefold() == "current" and (install / "sq.version").is_file()
            and (install.parent / "Update.exe").is_file()):
        return install.parent
    return install


def prepare_environment():
    override = os.environ.get(DATA_DIR_ENV, "").strip()
    frozen = getattr(sys, "frozen", False)
    if frozen:
        install = Path(sys.executable).parent
    else:
        get_install_folder = _module_imports.load('get_install_folder')
        install = Path(get_install_folder())
    if override:
        target = Path(override).expanduser().resolve()
    elif not frozen or sys.platform == "win32":
        target = storage_install_folder(install) / "data"
    elif sys.platform == "darwin":
        target = Path.home() / "Library" / "Application Support" / APP_ID
    else:
        target = Path(os.environ.get("XDG_DATA_HOME", Path.home() / ".local/share")) / APP_ID

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
        target = Path(os.environ.get("LOCALAPPDATA", Path.home() / "AppData/Local")) / APP_ID
        initialize(target)
    os.environ[DATA_DIR_ENV] = str(target)
    return target


def record_startup_error(folder, error):
    traceback = _module_imports.load('traceback')
    path = folder / "logs" / "startup-error.log"
    path.write_text("".join(traceback.format_exception(error)), encoding="utf-8")
    return path
