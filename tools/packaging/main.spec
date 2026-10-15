# -*- mode: python ; coding: utf-8 -*-

import os
import sys
import tempfile
from pathlib import Path


project_root = str(Path(SPECPATH).resolve().parents[1])
if project_root not in sys.path:
    sys.path.insert(0, project_root)

import anclicker  # Enable source-tree legacy entry points.

from anclicker.instructions.registry import hidden_imports as instruction_hidden_imports, ui_hidden_imports
from anclicker.app.compatibility import COMPATIBILITY_MODULES
from tools.import_policy import hidden_imports as centralized_hidden_imports
from info import (CURRENT_VERSION, APP_ID, APP_NAME, EXECUTABLE_NAME, VERSION, WINDOWS_VERSION,
                  COMPANY_NAME, COPYRIGHT, MACOS_BUNDLE_ID, UPDATE_CONFIG, update_source_config)
from PyInstaller.utils.hooks import collect_submodules, collect_data_files, collect_dynamic_libs
from anclicker.storage.database import DatabaseOperation

# Never bundle a developer's live commands or recording data in a release.
# Keep the temporary directory alive until Analysis/COLLECT finish.
seed_directory = tempfile.TemporaryDirectory(prefix='anclicker-release-seed-')
fresh_seed = Path(seed_directory.name) / '命令集.db'
DatabaseOperation(str(fresh_seed))
# Stable input paths allow Analysis caching. Always regenerate and compare the
# blank seed so a stale or modified cached database is never silently bundled.
seed_cache = Path(project_root) / 'artifacts/build/release-seed'
seed_cache.mkdir(parents=True, exist_ok=True)
def stable_seed(name, content):
    target = seed_cache / name
    if not target.is_file() or target.read_bytes() != content:
        target.write_bytes(content)
    return str(target)
seed_database = stable_seed('命令集.db', fresh_seed.read_bytes())


def collect_resource_datas():
    resources = Path(project_root) / 'resources'
    return [(str(path), str(path.parent.relative_to(project_root)))
            for path in resources.rglob('*') if path.is_file()]


instruction_datas = collect_resource_datas()
instruction_datas.append((str(Path(project_root) / "legacy/background_dm_worker.py"), "legacy"))
# A separately configured Python interpreter cannot read this executable's PYZ.
# Collect the same maintained source files for that standalone worker as well.
for source in ('info.py', 'anclicker/__init__.py', 'anclicker/_imports.py', 'anclicker/app/__init__.py',
               'anclicker/app/paths.py', 'anclicker/platform/__init__.py',
               'anclicker/platform/background_catalog.py',
               'anclicker/platform/background_dm_worker.py'):
    relative = Path(source)
    instruction_datas.append((str(Path(project_root) / relative), str(relative.parent)))
# The locally verified external DLLs and local registration configuration are not public build inputs.
# Native Qt editors call the isolated reference engine; bundle its sources and runtime.
rpa_root = Path(project_root) / 'integrations' / 'yingdao'
rpa_runtime = Path(project_root) / '.local/runtimes/electron'
if not rpa_runtime.is_dir():
    raise RuntimeError('Missing RPA runtime; run tools/setup_rpa_runtime.py before packaging')
for folder in ((rpa_root, rpa_runtime) if sys.platform == 'win32' else (rpa_root,)):
    for resource in folder.rglob('*'):
        if resource.is_file() and resource.suffix not in {'.log', '.pyc'}:
            instruction_datas.append((str(resource), str(Path('runtime') / resource.parent.relative_to(rpa_runtime.parent)) if folder == rpa_runtime else str(resource.parent.relative_to(project_root))))
import rapidocr_onnxruntime
rapid_source = Path(project_root) / '.local/models/rapidocr'
if not rapid_source.is_dir():
    rapid_source = Path(rapidocr_onnxruntime.__file__).parent / 'models'
instruction_datas.extend((str(path), 'ocr_models/rapidocr') for path in rapid_source.glob('*.onnx'))
# Native WeChat components remain local opt-in, not publicly redistributed.
if sys.platform == 'win32' and os.environ.get('ANCLICKER_BUNDLE_WXOCR') == '1':
    instruction_datas.append((str(Path(project_root)/'.local/models/wechat'), 'ocr_models/wechat'))
if sys.platform == 'win32':
    import json
    source_snapshot = stable_seed(UPDATE_CONFIG['snapshot_name'],
                                  json.dumps(update_source_config(), sort_keys=True).encode('utf-8'))
    instruction_datas.append((source_snapshot, '.'))
dynamic_instruction_imports = list(instruction_hidden_imports())
dynamic_instruction_imports += list(ui_hidden_imports())
icon_path = os.path.join(project_root, 'resources', 'clicker.ico') if sys.platform == 'win32' else None


windows_runtime_binaries = []
if sys.platform == 'win32':
    # Resolve from pinned wheels/CPython, never from the build host's System32.
    import PySide2
    from importlib.metadata import version as package_version
    if sys.version_info[:3] != (3, 10, 11) or package_version('PySide2') != '5.15.2.1':
        raise RuntimeError('Windows compatibility builds require Python 3.10.11 / PySide2 5.15.2.1')
    qt_root = Path(PySide2.__file__).parent
    runtime_sources = {name: qt_root / name for name in (
        'msvcp140.dll', 'msvcp140_1.dll', 'msvcp140_2.dll',
        'msvcp140_codecvt_ids.dll', 'concrt140.dll')}
    runtime_sources.update({name: Path(sys.base_prefix) / name for name in (
        'vcruntime140.dll', 'vcruntime140_1.dll')})
    for name, path in runtime_sources.items():
        if not path.is_file():
            raise RuntimeError(f'Missing redistributable runtime: {path}')
        windows_runtime_binaries.append((str(path), '.'))

a = Analysis(
    [os.path.join(project_root, 'main.py')],
    pathex=[project_root, str(Path(project_root) / "legacy")],
    binaries=collect_dynamic_libs('onnxruntime') + windows_runtime_binaries,
    datas=[
        (seed_database, 'defaults'),
    ] + instruction_datas + collect_data_files('rapidocr_onnxruntime', excludes=['models/**']),
    # Compatibility shims resolve their implementations through importlib.
    # Include the canonical package so source/frozen module lookup stays equal.
    hiddenimports=[*COMPATIBILITY_MODULES, *collect_submodules('anclicker'), *centralized_hidden_imports(project_root, excluded=('anclicker.platform.qt_compat.QtTest', 'qt_compat.QtTest')), 'Start_Win', 'pyttsx4.drivers', *dynamic_instruction_imports,
                   *collect_submodules('pynput'), *collect_submodules('rapidocr_onnxruntime'),
                   'local_ocr_worker', 'onnxruntime', 'tkinter'],
    hookspath=[],
    hooksconfig={},
    runtime_hooks=[],
    # PyInstaller 6.12 appends __main__ to this list during analysis. Include it
    # up front so the persisted list matches and does not invalidate every run.
    excludes=['anclicker_private_agent', 'qiniu', '发布Velopack', '__main__', 'qt_compat.QtTest', 'anclicker.platform.qt_compat.QtTest',
              *(['PySide6', 'shiboken6', 'PyQt5', 'PyQt6'] if sys.platform == 'win32'
                else ['PySide2', 'shiboken2', 'PyQt5', 'PyQt6'])],
    noarchive=False,
    optimize=0,
)
pyz = PYZ(a.pure)

windows_version = None
if sys.platform == 'win32':
    from PyInstaller.utils.win32.versioninfo import (VSVersionInfo, FixedFileInfo,
        StringFileInfo, StringTable, StringStruct, VarFileInfo, VarStruct)
    windows_version = VSVersionInfo(
        ffi=FixedFileInfo(filevers=WINDOWS_VERSION, prodvers=WINDOWS_VERSION,
                         mask=0x3f, flags=0, OS=0x40004, fileType=1, subtype=0, date=(0, 0)),
        kids=[StringFileInfo([StringTable('080404B0', [
            StringStruct('CompanyName', COMPANY_NAME), StringStruct('FileDescription', APP_NAME),
            StringStruct('FileVersion', VERSION + '.0'), StringStruct('ProductVersion', VERSION),
            StringStruct('InternalName', APP_ID), StringStruct('OriginalFilename', EXECUTABLE_NAME),
            StringStruct('ProductName', APP_NAME), StringStruct('LegalCopyright', COPYRIGHT),
        ])]), VarFileInfo([VarStruct('Translation', [2052, 1200])])])

exe = EXE(
    pyz,
    a.scripts,
    [],
    exclude_binaries=True,
    name=APP_ID,
    debug=False,
    bootloader_ignore_signals=False,
    strip=False,
    upx=True,
    console=False,
    disable_windowed_traceback=False,
    argv_emulation=False,
    target_arch=None,
    codesign_identity=None,
    entitlements_file=None,
    contents_directory='.',
    uac_admin=False,
    icon=icon_path,
    version=windows_version,
    manifest=str(Path(project_root) / 'tools/packaging/windows.manifest') if sys.platform == 'win32' else None,
)
coll = COLLECT(
    exe,
    a.binaries,
    a.datas,
    strip=False,
    upx=True,
    upx_exclude=[],
    name=APP_ID,
)

if sys.platform == 'darwin':
    app = BUNDLE(
        coll,
        name=f'{APP_ID}.app',
        # The PyInstaller wheel used by GitHub's Intel runner does not ship
        # the fallback icon-windowed.icns.  Supplying our Windows icon is
        # portable: PyInstaller converts it to ICNS through Pillow on macOS.
        icon=os.path.join(project_root, 'resources', 'clicker.ico'),
        bundle_identifier=MACOS_BUNDLE_ID,
        info_plist={
            'CFBundleShortVersionString': CURRENT_VERSION.lstrip('v'),
            'CFBundleVersion': CURRENT_VERSION.lstrip('v'),
            'NSHighResolutionCapable': True,
            'NSHumanReadableCopyright': COPYRIGHT,
        },
    )

# Keep Electron's native framework layout and signatures intact on Unix.
# Passing its libraries through Analysis rewrites dependencies and drops
# framework directory symlinks that Electron needs at startup.
if sys.platform != 'win32':
    import shutil
    runtime_parent = (Path(DISTPATH) / f'{APP_ID}.app' / 'Contents' / 'Resources'
                      if sys.platform == 'darwin' else Path(DISTPATH) / APP_ID)
    shutil.copytree(rpa_runtime, runtime_parent / 'runtime' / 'electron',
                    symlinks=True, dirs_exist_ok=True)
    if sys.platform == 'darwin':
        import subprocess
        subprocess.run(['codesign', '--force', '--sign', '-',
                        str(Path(DISTPATH) / f'{APP_ID}.app')], check=True)
