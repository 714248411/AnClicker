"""Create a deterministic ZIP artifact from the current platform build."""

from __future__ import annotations

import argparse
import json
import os
import platform
import stat
import sys
import zipfile
from pathlib import Path


PROJECT_ROOT = Path(__file__).resolve().parents[1]
DIST_ROOT = PROJECT_ROOT / "dist"
RELEASE_ROOT = PROJECT_ROOT / "release"


def platform_label() -> str:
    system_ = platform.system().lower()
    machine_ = platform.machine().lower().replace("amd64", "x64").replace("x86_64", "x64")
    if system_ == "windows":
        return f"windows-{machine_}"
    if system_ == "darwin":
        return f"macos-{machine_}"
    if system_ == "linux":
        return f"linux-{machine_}"
    return f"{system_}-{machine_}"


def build_root() -> Path:
    app_bundle_ = DIST_ROOT / "AnClicker.app"
    app_directory_ = DIST_ROOT / "AnClicker"
    if sys.platform == "darwin" and app_bundle_.exists():
        return app_bundle_
    if app_directory_.exists():
        return app_directory_
    raise FileNotFoundError("未找到 dist/AnClicker 或 dist/AnClicker.app，请先运行 PyInstaller")


def add_tree(archive_: zipfile.ZipFile, source_: Path, prefix_: str) -> None:
    for path_ in sorted(source_.rglob("*")):
        relative_ = path_.relative_to(source_)
        archive_name_ = Path(prefix_) / relative_
        if path_.is_dir():
            continue
        info_ = zipfile.ZipInfo.from_file(path_, archive_name_.as_posix())
        if os.access(path_, os.X_OK):
            info_.external_attr = (stat.S_IFREG | 0o755) << 16
        with path_.open("rb") as source_file_:
            archive_.writestr(info_, source_file_.read(), compress_type=zipfile.ZIP_DEFLATED)


def main() -> int:
    parser_ = argparse.ArgumentParser()
    parser_.add_argument("--version", default="v1.0.0-beta.1")
    arguments_ = parser_.parse_args()

    source_ = build_root()
    label_ = platform_label()
    RELEASE_ROOT.mkdir(exist_ok=True)
    archive_path_ = RELEASE_ROOT / f"AnClicker-{arguments_.version}-{label_}.zip"
    manifest_ = {
        "application": "An Clicker",
        "version": arguments_.version,
        "platform": label_,
        "python": platform.python_version(),
        "entry": "AnClicker.exe" if sys.platform == "win32" else "AnClicker",
    }
    with zipfile.ZipFile(archive_path_, "w", allowZip64=True) as archive_:
        add_tree(archive_, source_, source_.name)
        archive_.writestr(
            "BUILD-MANIFEST.json",
            json.dumps(manifest_, ensure_ascii=False, indent=2).encode("utf-8"),
        )
    print(archive_path_)
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
