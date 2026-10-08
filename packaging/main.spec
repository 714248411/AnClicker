# -*- mode: python ; coding: utf-8 -*-

import os
import sys
import tempfile


project_root = os.path.dirname(os.path.abspath(SPECPATH))
if project_root not in sys.path:
    sys.path.insert(0, project_root)

from instructions.registry import hidden_imports as instruction_hidden_imports
from info import CURRENT_VERSION
from PyInstaller.utils.hooks import collect_submodules, collect_data_files, collect_dynamic_libs
from 数据库操作 import DatabaseOperation

# Never bundle a developer's live commands or recording data in a release.
# Keep the temporary directory alive until Analysis/COLLECT finish.
seed_directory = tempfile.TemporaryDirectory(prefix='anclicker-release-seed-')
seed_database = os.path.join(seed_directory.name, '命令集.db')
DatabaseOperation(seed_database)


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
dynamic_instruction_imports = list(instruction_hidden_imports())
app_name = 'AnClicker'
icon_path = os.path.join(project_root, 'clicker.ico') if sys.platform == 'win32' else None


a = Analysis(
    [os.path.join(project_root, 'main.py')],
    pathex=[project_root],
    binaries=collect_dynamic_libs('onnxruntime'),
    datas=[
        (seed_database, 'data'),
        (os.path.join(project_root, 'flat', 'Combinear.qss'), 'flat'),
        (os.path.join(project_root, 'flat', 'chevron-down.svg'), 'flat'),
        (os.path.join(project_root, 'flat', 'chevron-up.svg'), 'flat'),
        (os.path.join(project_root, 'flat', '开屏.png'), 'flat'),
        (os.path.join(project_root, 'Window', 'res', 'donation_qr.png'), 'Window/res'),
    ] + instruction_datas + collect_data_files('rapidocr_onnxruntime'),
    hiddenimports=['Start_Win', 'pyttsx4.drivers', *dynamic_instruction_imports,
                   *collect_submodules('pynput'), *collect_submodules('rapidocr_onnxruntime'),
                   'local_ocr_worker', 'onnxruntime'],
    hookspath=[],
    hooksconfig={},
    runtime_hooks=[],
    excludes=[],
    noarchive=False,
    optimize=0,
)
pyz = PYZ(a.pure)

exe = EXE(
    pyz,
    a.scripts,
    [],
    exclude_binaries=True,
    name=app_name,
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
    version=os.path.join(project_root, 'packaging', 'windows-version.txt') if sys.platform == 'win32' else None,
)
coll = COLLECT(
    exe,
    a.binaries,
    a.datas,
    strip=False,
    upx=True,
    upx_exclude=[],
    name=app_name,
)

if sys.platform == 'darwin':
    app = BUNDLE(
        coll,
        name=f'{app_name}.app',
        # The PyInstaller wheel used by GitHub's Intel runner does not ship
        # the fallback icon-windowed.icns.  Supplying our Windows icon is
        # portable: PyInstaller converts it to ICNS through Pillow on macOS.
        icon=os.path.join(project_root, 'clicker.ico'),
        bundle_identifier='com.yanyi.anclicker',
        info_plist={
            'CFBundleShortVersionString': CURRENT_VERSION.lstrip('v'),
            'CFBundleVersion': CURRENT_VERSION.lstrip('v'),
            'NSHighResolutionCapable': True,
            'NSHumanReadableCopyright': 'Copyright © 2022–2026 YanYi and contributors',
        },
    )
