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
    global DIST_ROOT
    parser_ = argparse.ArgumentParser()
    parser_.add_argument("--version", default="v1.2.1")
    parser_.add_argument("--dist", type=Path, default=DIST_ROOT)
    arguments_ = parser_.parse_args()
    DIST_ROOT = arguments_.dist.resolve()
    source_ = build_root()
    label_ = platform_label()
    RELEASE_ROOT.mkdir(exist_ok=True)
    archive_path_ = RELEASE_ROOT / f"AnClicker-{arguments_.version}-{label_}.zip"
    manifest_ = {
        "application": "An Clicker",
        "package_type": "full-application",
        "version": arguments_.version,
        "platform": label_,
        "python": platform.python_version(),
        "entry": "AnClicker.exe" if sys.platform == "win32" else "AnClicker",
    }
    with zipfile.ZipFile(archive_path_, "w", allowZip64=True) as archive_:
        add_tree(archive_, source_, source_.name)
        tool_prefix = '旧版数据迁移工具/'
        archive_.writestr(tool_prefix + '使用说明.txt',
            ('此文件夹与 AnClicker 主程序文件夹保持并列，请完整解压压缩包。\n'
             'Windows 双击启动迁移器.cmd；macOS/Linux 在终端运行 bash 启动迁移器.sh。\n'
             '选择旧版 Excel 和输出目录；转换后查看迁移报告，再导入主程序。\n'
             '原文件会备份，多个独立分支分别输出；缺失图片需要补齐。\n'
             '跨分支跳转及未知指令可能无法转换，以报告为准。\n').encode('utf-8'))
        if sys.platform == 'win32':
            archive_.writestr(tool_prefix + '启动迁移器.cmd',
                '@echo off\r\nstart "" "%~dp0..\\AnClicker\\AnClicker.exe" --migration-tool\r\n')
        else:
            entry = '../AnClicker.app/Contents/MacOS/AnClicker' if sys.platform == 'darwin' else '../AnClicker/AnClicker'
            info = zipfile.ZipInfo(tool_prefix + '启动迁移器.sh')
            info.external_attr = (stat.S_IFREG | 0o755) << 16
            archive_.writestr(info, '#!/bin/sh\ncd -- "$(dirname -- "$0")" || exit 1\nexec "' + entry + '" --migration-tool\n')
        archive_.writestr(
            "BUILD-MANIFEST.json",
            json.dumps(manifest_, ensure_ascii=False, indent=2).encode("utf-8"),
        )
    print(archive_path_)
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
