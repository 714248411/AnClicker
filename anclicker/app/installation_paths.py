"""Installation path helpers with no storage initialization or GUI imports."""
import os
import sys
from pathlib import Path


def storage_install_folder(install):
    # Portable user data must live outside Velopack's replaceable current folder.
    if (install.name.casefold() == "current" and (install / "sq.version").is_file()
            and (install.parent / "Update.exe").is_file()):
        return install.parent
    return install


def get_install_folder() -> str:
    """获取程序安装目录。"""
    if getattr(sys, "frozen", False):
        return os.path.dirname(sys.executable)
    return str(Path(__file__).resolve().parents[2])

