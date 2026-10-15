"""Lightweight application paths; importing this module performs no I/O."""
import os
import sys
import shutil
from pathlib import Path
from info import APP_ID, DATA_DIR_ENV

from anclicker._imports import DeferredImports as _DeferredImports

# Dependencies declared here retain their existing on-demand loading boundaries.
_module_imports = _DeferredImports(globals(), {
    'storage_install_folder': ('from', 'anclicker.app.startup_environment', ('storage_install_folder',), 0),
    'Path': ('from', 'pathlib', ('Path',), 0),
})


def get_install_folder() -> str:
    """获取程序安装目录。"""
    if getattr(sys, "frozen", False):
        return os.path.dirname(sys.executable)
    return str(Path(__file__).resolve().parents[2])


def get_resource_folder() -> str:
    """获取只读程序资源目录。"""
    if getattr(sys, "frozen", False):
        return getattr(sys, "_MEIPASS", os.path.dirname(sys.executable))
    return str(Path(__file__).resolve().parents[2])


INSTALL_FOLDER = get_install_folder()
RESOURCE_FOLDER = get_resource_folder()


def get_platform_data_folder() -> str:
    """Return a writable per-user data directory on each supported desktop OS."""
    override_ = os.environ.get(DATA_DIR_ENV, "").strip()
    if override_:
        return os.path.abspath(os.path.expanduser(override_))
    if not getattr(sys, "frozen", False):
        return os.path.join(INSTALL_FOLDER, "data")
    if sys.platform == "win32":
        # Keep compatibility with existing portable Windows releases.
        storage_install_folder = _module_imports.load('storage_install_folder')
        Path = _module_imports.load('Path')
        return str(storage_install_folder(Path(INSTALL_FOLDER)) / "data")
    if sys.platform == "darwin":
        return os.path.join(
            os.path.expanduser("~/Library/Application Support"), APP_ID
        )
    xdg_data_home_ = os.environ.get(
        "XDG_DATA_HOME", os.path.expanduser("~/.local/share")
    )
    return os.path.join(xdg_data_home_, APP_ID)


DATA_FOLDER = get_platform_data_folder()
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
    seed_database_ = os.path.join(RESOURCE_FOLDER, "defaults", "命令集.db")
    if not os.path.exists(DATABASE_PATH) and os.path.isfile(seed_database_):
        shutil.copy2(seed_database_, DATABASE_PATH)



def resource_path(*parts: str) -> Path:
    relative = Path(*parts).as_posix()
    aliases = {
        'flat/Combinear.qss': 'resources/styles/Combinear.qss',
        'flat/chevron-down.svg': 'resources/icons/chevron-down.svg',
        'flat/chevron-up.svg': 'resources/icons/chevron-up.svg',
        'flat/startup.gif': 'resources/animations/startup.gif',
        'flat/startup-fallback.png': 'resources/animations/startup-fallback.png',
    }
    for old, new in (('Window/res/', 'resources/images/windows/'),
                     ('Window/qss_icons/', 'resources/icons/windows/'),
                     ('Window/flatwhite/', 'resources/styles/window-flatwhite/')):
        if relative.startswith(old):
            relative = new + relative[len(old):]
            break
    return Path(get_resource_folder()) / aliases.get(relative, relative)


def runtime_path(name: str) -> Path:
    """Locate local development runtimes or the delivered runtime layout."""
    if getattr(sys, 'frozen', False):
        root = Path(get_resource_folder())
        if sys.platform == 'darwin':
            root = root.parent / 'Resources'
        return root / 'runtime' / name
    return Path(get_install_folder()) / '.local/runtimes' / name


def model_path(name: str) -> Path:
    """Locate offline model files without changing writable application data."""
    if getattr(sys, 'frozen', False):
        return Path(get_resource_folder()) / 'ocr_models' / name
    return Path(get_install_folder()) / '.local/models' / name
