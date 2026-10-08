"""通用发布门槛：产物安全、真实 EXE 启动和可用的差量包还原。"""

from __future__ import annotations

import json
from contextlib import closing
import os
import struct
import subprocess
import tempfile
import time
import zipfile
from dataclasses import dataclass
from pathlib import Path, PurePosixPath
from info import UPDATE_CONFIG, update_source_config


@dataclass(frozen=True)
class ReleaseContext:
    project_root: Path
    app_dir: Path
    release_dir: Path
    portable_zip: Path
    program_title: str
    pack_id: str
    version: str
    runtime: str


def allow_project_artifact(relative_path: PurePosixPath) -> bool:
    """业务项目可在此明确允许经过审核的只读资源。默认不放行。"""
    parts = relative_path.parts
    if parts[:2] == ('lib', 'app'):
        parts = parts[2:]
    elif parts[:1] == ('current',):
        parts = parts[1:]
    # Generated seed and OpenCV's packaged read-only Python initializer only.
    return parts in {('defaults', '命令集.db'), ('cv2', 'data'), ('cv2', 'data', '__init__.py')}


def validate_project_release(context: ReleaseContext) -> None:
    """业务项目在此增加数据库迁移、插件或业务协议等专属检查。"""
    # The sole database exception is a generated, empty seed, never user storage.
    import sqlite3
    database = context.app_dir / 'defaults' / '命令集.db'
    from 数据库操作 import DatabaseOperation
    with tempfile.TemporaryDirectory() as folder:
        expected = Path(folder) / 'expected.db'
        DatabaseOperation(str(expected))
        with closing(sqlite3.connect(database)) as actual, closing(sqlite3.connect(expected)) as clean:
            if list(actual.iterdump()) != list(clean.iterdump()):
                raise RuntimeError('打包数据库不是空白默认数据库')


def _check_member(name: str) -> None:
    normalized = name.replace("\\", "/")
    path = PurePosixPath(normalized)
    if not path.parts or normalized.startswith("/") or ".." in path.parts or ":" in path.parts[0]:
        raise RuntimeError(f"发布包包含不安全路径: {name}")
    lower = PurePosixPath(normalized.casefold())
    if allow_project_artifact(lower):
        return
    parts = lower.parts
    if not parts:
        return
    filename = parts[-1]
    # 用户数据不应进入程序目录或 current；defaults 中的只读示例不受影响。
    if "data" in parts or "profiles" in parts:
        raise RuntimeError(f"发布产物包含可变数据目录: {name}")
    if filename.endswith((
        ".db", ".sqlite", ".sqlite3", ".db-wal", ".db-shm", ".db-journal", ".db.bak"
    )):
        raise RuntimeError(f"发布产物包含数据库文件: {name}")


def validate_directory(path: Path) -> None:
    for member in path.rglob("*"):
        _check_member(member.relative_to(path).as_posix())


def validate_archive(path: Path) -> None:
    with zipfile.ZipFile(path) as archive:
        bad_member = archive.testzip()
        if bad_member:
            raise RuntimeError(f"发布包 CRC 校验失败: {path.name}: {bad_member}")
        for member in archive.namelist():
            checked = member
            if path.name.endswith('-delta.nupkg'):
                for suffix in ('.diff', '.shasum'):
                    if checked.endswith(suffix):
                        checked = checked[:-len(suffix)]
                        break
            _check_member(checked)


def validate_windowed_executable(path: Path) -> None:
    with path.open("rb") as stream:
        if stream.read(2) != b"MZ":
            raise RuntimeError(f"不是 Windows EXE: {path}")
        stream.seek(0x3C)
        pe_offset = struct.unpack("<I", stream.read(4))[0]
        stream.seek(pe_offset)
        if stream.read(4) != b"PE\0\0":
            raise RuntimeError(f"Windows PE 文件头无效: {path}")
        stream.seek(pe_offset + 24 + 68)
        subsystem = struct.unpack("<H", stream.read(2))[0]
    if subsystem != 2:
        raise RuntimeError(f"主程序必须使用 Windows GUI 子系统: {path}")


def _smoke_executable(executable: Path, context: ReleaseContext, sandbox: Path, *, launcher: bool = False, full_checks: bool = False) -> None:
    sandbox.mkdir(parents=True, exist_ok=True)
    data_dir = sandbox / "data"
    report = data_dir / "startup-ready.json"
    environment = os.environ.copy()
    environment.update({
        "ANCLICKER_DATA_DIR": str(data_dir),
        "ANCLICKER_SMOKE_LIGHTWEIGHT": "0" if full_checks else "1",
        "ANCLICKER_SINGLETON_KEY": "release-" + __import__("uuid").uuid4().hex,
        
        "QT_QPA_PLATFORM": "windows",
        "APPDATA": str(sandbox / "AppData" / "Roaming"),
        "LOCALAPPDATA": str(sandbox / "AppData" / "Local"),
        "TEMP": str(sandbox / "temp"),
        "TMP": str(sandbox / "temp"),
    })
    for key in ("APPDATA", "LOCALAPPDATA", "TEMP"):
        Path(environment[key]).mkdir(parents=True, exist_ok=True)

    def launch() -> None:
        report.unlink(missing_ok=True)
        subprocess.run(
            [str(executable), "--release-smoke"], cwd=sandbox, env=environment,
            check=True, timeout=45,
        )
        if launcher:
            deadline = time.monotonic() + 45
            while not report.is_file() and time.monotonic() < deadline:
                time.sleep(0.1)
            # The root launcher exits before its child. Wait for the actual app
            # to release the portable directory before the next launch/cleanup.
            import psutil
            actual_exe = (executable.parent / 'current' / f'{context.program_title}.exe').resolve()
            while time.monotonic() < deadline:
                children = []
                for process in psutil.process_iter(['exe']):
                    if process.info['exe'] and Path(process.info['exe']).resolve() == actual_exe:
                        children.append(process)
                if not children:
                    break
                time.sleep(0.1)
            else:
                raise RuntimeError('Portable launcher child did not exit after smoke validation')
        if not report.is_file():
            raise RuntimeError(f"实际 EXE 未生成启动自检报告: {executable}")
        result = json.loads(report.read_text(encoding="utf-8"))
        if (
            result.get("ok") is not True
            or result.get("window_visible") is not True
            or result.get("window_chrome_valid") is not True
            or (environment["ANCLICKER_SMOKE_LIGHTWEIGHT"] == "0" and result.get("full_checks") is not True)
            or result.get("version") != context.version
            or result.get("update_config") != update_source_config()
            or Path(result.get("data_root", "")).resolve() != data_dir.resolve()
        ):
            raise RuntimeError(f"实际 EXE 启动自检失败: {executable}: {result}")

    launch()
    environment["ANCLICKER_SMOKE_LIGHTWEIGHT"] = "1"
    import sqlite3
    with closing(sqlite3.connect(data_dir / '命令集.db')) as db:
        db.execute('CREATE TABLE release_retention (value TEXT)')
        db.execute("INSERT INTO release_retention VALUES ('preserved')")
        db.commit()
    sentinel = data_dir / "release-sentinel.txt"
    sentinel.write_text("retain-user-data", encoding="utf-8")
    launch()
    with closing(sqlite3.connect(data_dir / '命令集.db')) as db:
        if db.execute('SELECT value FROM release_retention').fetchone() != ('preserved',):
            raise RuntimeError('重复启动未保留用户数据库')
    if sentinel.read_text(encoding="utf-8") != "retain-user-data":
        raise RuntimeError("重复启动覆盖了用户文件")


def _validate_delta(context: ReleaseContext, sandbox: Path, *, app_version: str | None = None) -> None:
    sandbox.mkdir(parents=True, exist_ok=True)
    current = context.release_dir / f"{context.pack_id}-{context.version}-{context.runtime}-full.nupkg"
    delta = context.release_dir / f"{context.pack_id}-{context.version}-{context.runtime}-delta.nupkg"
    if not delta.is_file():
        print("未生成 delta，跳过差量还原检查；完整包仍已验证。")
        return
    bases = [
        path for path in context.release_dir.glob(f"{context.pack_id}-*-{context.runtime}-full.nupkg")
        if path != current
    ]
    if len(bases) != 1:
        raise RuntimeError("delta 存在，但上一版 full 基线数量不是 1")
    rebuilt = sandbox / "rebuilt.nupkg"
    subprocess.run(
        ["dotnet", "tool", "run", "vpk", "delta", "patch", "--base", str(bases[0]),
         "--patch", str(delta), "--output", str(rebuilt)],
        cwd=context.project_root, check=True, timeout=180,
    )
    with zipfile.ZipFile(current) as expected, zipfile.ZipFile(rebuilt) as actual:
        expected_names = {name for name in expected.namelist() if not name.endswith("/")}
        actual_names = {name for name in actual.namelist() if not name.endswith("/")}
        if expected_names != actual_names:
            raise RuntimeError("差量还原后的文件集合与 full 包不同")
        for name in expected_names:
            if expected.read(name) != actual.read(name):
                raise RuntimeError(f"差量还原内容与 full 包不同: {name}")
        matching_exe = [
            name for name in actual_names
            if name.casefold().endswith(f"/{context.program_title}.exe".casefold())
        ]
        if len(matching_exe) != 1:
            raise RuntimeError("差量还原包中主程序数量不是 1")
        patched_root = sandbox / "patched"
        actual.extractall(patched_root)
    from dataclasses import replace
    smoke_context = replace(context, version=app_version) if app_version else context
    _smoke_executable(patched_root / matching_exe[0], smoke_context, sandbox / "patched-smoke")


def validate_portable_release(context: ReleaseContext) -> None:
    if any(path.name.casefold().endswith('-setup.exe') for path in context.release_dir.iterdir()):
        raise RuntimeError('便携版发布不应生成 Setup.exe')
    assets = json.loads((context.release_dir / f'assets.{context.runtime}.json').read_text(encoding='utf-8-sig'))
    if not isinstance(assets, list) or not all(isinstance(asset, dict) for asset in assets):
        raise RuntimeError('资产清单必须是对象数组')
    types = {str(asset.get('Type', '')).casefold() for asset in assets}
    if 'portable' not in types or 'installer' in types:
        raise RuntimeError('资产清单必须包含 portable 且不能包含 installer')
    required = {'.portable', 'Update.exe', UPDATE_CONFIG['launcher_name'],
                f'current/{context.program_title}.exe', 'current/sq.version'}
    with zipfile.ZipFile(context.portable_zip) as archive:
        missing = required - set(archive.namelist())
    if missing:
        raise RuntimeError('便携包缺少必要文件: ' + ', '.join(sorted(missing)))


def validate_release(context: ReleaseContext) -> None:
    from validation_cache import verify_once
    verify_once(context, 'startup', lambda: _validate_release(context))


def _validate_release(context: ReleaseContext) -> None:
    """在构建后和发布前调用；任何失败均阻止上传。"""
    executable = context.app_dir / f"{context.program_title}.exe"
    if not executable.is_file():
        raise FileNotFoundError(executable)
    validate_portable_release(context)
    validate_project_release(context)
    validate_directory(context.app_dir)
    validate_windowed_executable(executable)
    current = context.release_dir / f"{context.pack_id}-{context.version}-{context.runtime}-full.nupkg"
    if not current.is_file():
        raise FileNotFoundError(current)
    for package in context.release_dir.glob(f"{context.pack_id}-{context.version}-{context.runtime}-*.nupkg"):
        validate_archive(package)
    validate_archive(context.portable_zip)
    with tempfile.TemporaryDirectory(prefix="velopack-release-gate-") as temporary:
        sandbox = Path(temporary)
        _smoke_executable(executable, context, sandbox / "onedir", full_checks=True)
        portable_root = sandbox / "portable"
        with zipfile.ZipFile(context.portable_zip) as archive:
            archive.extractall(portable_root)
        # 根目录启动器会派生 current 中的程序并先行退出；直接检查实际程序，
        # 避免将启动器退出码误认为窗口自检完成。
        _smoke_executable(
            portable_root / "current" / f"{context.program_title}.exe",
            context,
            sandbox / "portable-smoke",
        )
        _smoke_executable(portable_root / UPDATE_CONFIG['launcher_name'], context,
                          sandbox / 'launcher-smoke', launcher=True)
        _validate_delta(context, sandbox)
    validate_project_release(context)
    print("通用发布门槛通过：产物安全、实际 EXE 启动与数据保留。")
