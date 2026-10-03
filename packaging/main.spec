# -*- mode: python ; coding: utf-8 -*-

import os
import sys


project_root = os.path.dirname(os.path.abspath(SPECPATH))
if project_root not in sys.path:
    sys.path.insert(0, project_root)

from instructions.registry import hidden_imports as instruction_hidden_imports


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


a = Analysis(
    [os.path.join(project_root, 'main.py')],
    pathex=[project_root],
    binaries=[],
    datas=[
        (os.path.join(project_root, 'data', '命令集.db'), 'data'),
        (os.path.join(project_root, 'flat', 'Combinear.qss'), 'flat'),
        (os.path.join(project_root, 'flat', '开屏.png'), 'flat'),
    ] + instruction_datas,
    hiddenimports=['pyttsx4.drivers', *dynamic_instruction_imports],
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
    name='Clicker',
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
    uac_admin=True,
    icon=os.path.join(project_root, 'clicker.ico'),
)
coll = COLLECT(
    exe,
    a.binaries,
    a.datas,
    strip=False,
    upx=True,
    upx_exclude=[],
    name='Clicker',
)
