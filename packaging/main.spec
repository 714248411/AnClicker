# -*- mode: python ; coding: utf-8 -*-

import os
import sys
import tempfile
from pathlib import Path


project_root = os.path.dirname(os.path.abspath(SPECPATH))
if project_root not in sys.path:
    sys.path.insert(0, project_root)

from instructions.registry import hidden_imports as instruction_hidden_imports
from info import (CURRENT_VERSION, APP_ID, APP_NAME, EXECUTABLE_NAME, VERSION, WINDOWS_VERSION,
                  COMPANY_NAME, COPYRIGHT, MACOS_BUNDLE_ID, UPDATE_CONFIG, update_source_config)
from PyInstaller.utils.hooks import collect_submodules, collect_data_files, collect_dynamic_libs
from 数据库操作 import DatabaseOperation

# Never bundle a developer's live commands or recording data in a release.
# Keep the temporary directory alive until Analysis/COLLECT finish.
seed_directory = tempfile.TemporaryDirectory(prefix='anclicker-release-seed-')
fresh_seed = Path(seed_directory.name) / '命令集.db'
DatabaseOperation(str(fresh_seed))
# Stable input paths allow Analysis caching. Always regenerate and compare the
# blank seed so a stale or modified cached database is never silently bundled.
seed_cache = Path(project_root) / 'build' / 'release-seed'
seed_cache.mkdir(parents=True, exist_ok=True)
def stable_seed(name, content):
    target = seed_cache / name
    if not target.is_file() or target.read_bytes() != content:
        target.write_bytes(content)
    return str(target)
seed_database = stable_seed('命令集.db', fresh_seed.read_bytes())


def collect_instruction_datas():
    """收集独立指令编辑器 UI 和随模块发布的静态资源。"""
    instructions_root = os.path.join(project_root, 'instructions')
    collected = []
    for directory, subdirectories, filenames in os.walk(instructions_root):
        subdirectories[:] = sorted(
            name for name in subdirectories
            if name != '__pycache__' and not name.startswith('.')
        )
        destination = os.path.relpath(directory, project_root)
        for filename in sorted(filenames):
            suffix = os.path.splitext(filename)[1].lower()
            is_generated_ui = filename.endswith('_ui.py')
            is_static_resource = suffix not in {'.py', '.pyc', '.pyo'}
            if is_generated_ui or is_static_resource:
                collected.append((os.path.join(directory, filename), destination))
    return collected


instruction_datas = collect_instruction_datas()
import rapidocr_onnxruntime
rapid_source = Path(project_root) / 'ocr_models' / 'rapidocr'
if not rapid_source.is_dir():
    rapid_source = Path(rapidocr_onnxruntime.__file__).parent / 'models'
instruction_datas.extend((str(path), 'ocr_models/rapidocr') for path in rapid_source.glob('*.onnx'))
# Native WeChat components remain local opt-in, not publicly redistributed.
if sys.platform == 'win32' and os.environ.get('ANCLICKER_BUNDLE_WXOCR') == '1':
    instruction_datas.append((str(Path(project_root)/'ocr_models'/'wechat'), 'ocr_models/wechat'))
if sys.platform == 'win32':
    import json
    source_snapshot = stable_seed(UPDATE_CONFIG['snapshot_name'],
                                  json.dumps(update_source_config(), sort_keys=True).encode('utf-8'))
    instruction_datas.append((source_snapshot, '.'))
dynamic_instruction_imports = list(instruction_hidden_imports())
icon_path = os.path.join(project_root, 'clicker.ico') if sys.platform == 'win32' else None


a = Analysis(
    [os.path.join(project_root, 'main.py')],
    pathex=[project_root],
    binaries=collect_dynamic_libs('onnxruntime'),
    datas=[
        (seed_database, 'defaults'),
        (os.path.join(project_root, 'flat', 'Combinear.qss'), 'flat'),
        (os.path.join(project_root, 'flat', 'chevron-down.svg'), 'flat'),
        (os.path.join(project_root, 'flat', 'chevron-up.svg'), 'flat'),
        (os.path.join(project_root, 'flat', '开屏.png'), 'flat'),
        (os.path.join(project_root, 'Window', 'res', 'donation_qr.png'), 'Window/res'),
    ] + instruction_datas + collect_data_files('rapidocr_onnxruntime', excludes=['models/**']),
    hiddenimports=['Start_Win', 'pyttsx4.drivers', *dynamic_instruction_imports,
                   *collect_submodules('pynput'), *collect_submodules('rapidocr_onnxruntime'),
                   'local_ocr_worker', 'onnxruntime'],
    hookspath=[],
    hooksconfig={},
    runtime_hooks=[],
    # PyInstaller 6.12 appends __main__ to this list during analysis. Include it
    # up front so the persisted list matches and does not invalidate every run.
    excludes=['qiniu', '发布Velopack', '__main__'],
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
        icon=os.path.join(project_root, 'clicker.ico'),
        bundle_identifier=MACOS_BUNDLE_ID,
        info_plist={
            'CFBundleShortVersionString': CURRENT_VERSION.lstrip('v'),
            'CFBundleVersion': CURRENT_VERSION.lstrip('v'),
            'NSHighResolutionCapable': True,
            'NSHumanReadableCopyright': COPYRIGHT,
        },
    )
