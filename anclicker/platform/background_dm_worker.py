"""Isolated, single-threaded dm.dmsoft host; no UI or foreground fallback."""
import ctypes
import json
import os
from pathlib import Path
import struct
import sys
from anclicker.platform.background_catalog import METHODS

from anclicker._imports import DeferredImports as _DeferredImports

# Dependencies declared here retain their existing on-demand loading boundaries.
_module_imports = _DeferredImports(globals(), {
    'win32com': ('import', 'win32com.client', (), False),
    'pythoncom': ('import', 'pythoncom', (), False),
    'VARIANT': ('from', 'win32com.client', ('VARIANT',), 0),
})


ALLOWED = {'BindWindow', 'UnBindWindow', 'MoveTo', 'LeftClick', 'RightClick', 'MiddleClick',
           'LeftDown', 'LeftUp', 'RightDown', 'RightUp', 'MiddleDown', 'MiddleUp',
           'KeyDown', 'KeyUp', 'SendString', 'WheelUp', 'WheelDown', 'Capture', 'GetColor'}


def pe_bits(path):
    with open(path, 'rb') as stream:
        if stream.read(2) != b'MZ':
            raise RuntimeError('大漠 DLL 不是有效的 Windows 文件')
        stream.seek(0x3c)
        offset = struct.unpack('<I', stream.read(4))[0]
        stream.seek(offset)
        if stream.read(4) != b'PE\0\0':
            raise RuntimeError('大漠 DLL 格式无效')
        machine = struct.unpack('<H', stream.read(2))[0]
    if machine not in (0x14c, 0x8664):
        raise RuntimeError('不支持此大漠 DLL 架构')
    return 32 if machine == 0x14c else 64


def create_dm():
    if sys.platform != 'win32':
        raise RuntimeError('大漠后台功能仅支持 Windows')
    win32com = _module_imports.load('win32com')
    # Keep the loader alive for the entire COM object's lifetime.
    loader = None
    dll = os.environ.get('ANCLICKER_DM_DLL', '').strip()
    if dll:
        path = Path(dll).expanduser().resolve()
        if not path.is_file():
            raise RuntimeError('未找到配置的大漠 dm.dll')
        bits = pe_bits(path)
        if bits != struct.calcsize('P') * 8:
            raise RuntimeError(f'dm.dll 为 {bits} 位，请配置相同位数的后台 Python 运行环境')
        reg = path.with_name('DmReg.dll')
        if not reg.is_file():
            raise RuntimeError('免注册加载需要与 dm.dll 配套的 DmReg.dll')
        loader = ctypes.WinDLL(str(reg))
        loader.SetDllPathW.argtypes = [ctypes.c_wchar_p, ctypes.c_int]
        loader.SetDllPathW.restype = ctypes.c_int
        if loader.SetDllPathW(str(path), 1) != 1:
            raise RuntimeError('大漠免注册加载失败，请检查组件版本和位数')
    try:
        dm = win32com.client.Dispatch('dm.dmsoft')
    except Exception as exc:
        raise RuntimeError('无法加载大漠组件：请安装匹配位数的插件，或配置 dm.dll 与 DmReg.dll') from exc
    version = str(dm.Ver())
    code = os.environ.get('ANCLICKER_DM_REG_CODE', '')
    if code:
        result = int(dm.Reg(code, os.environ.get('ANCLICKER_DM_REG_EXTRA', '')))
        if result != 1:
            raise RuntimeError(f'大漠授权失败，返回码 {result}')
    elif version != '3.1233':
        raise RuntimeError('此大漠版本尚未配置授权，请先设置大漠注册码')
    return dm, loader, version


def main():
    pythoncom = _module_imports.load('pythoncom')
    pythoncom.CoInitialize()
    dm = loader = None
    try:
        for line in sys.stdin:
            try:
                request = json.loads(line)
                method = request['method']
                if method == 'init':
                    if dm is not None:
                        raise RuntimeError('后台组件已经初始化')
                    dm, loader, result = create_dm()
                elif dm is not None and (method in ALLOWED or method in METHODS):
                    arguments = list(request.get('args', []))
                    output = []
                    if request.get('raw') and method in METHODS:
                        definition = METHODS[method]
                        if len(arguments) != len(definition['args']):
                            raise RuntimeError('后台参数数量不正确')
                        for i, item in enumerate(definition['args']):
                            if item['out']:
                                VARIANT = _module_imports.load('VARIANT')
                                arguments[i] = VARIANT(pythoncom.VT_BYREF | pythoncom.VT_VARIANT,
                                                       arguments[i] if item.get("inout") else 0)
                                output.append((item['name'], arguments[i]))
                    result = getattr(dm, method)(*arguments)
                    if output:
                        result = {'value': result, 'output': {name: value.value for name, value in output}}
                    if not request.get('raw') and method != 'GetColor' and int(result) != 1:
                        raise RuntimeError(f'后台操作 {method} 失败，返回码 {result}')
                else:
                    raise RuntimeError('无效的后台调用')
                response = {'ok': True, 'result': result}
            except Exception as exc:
                # Do not return native COM argument dumps, which may contain credentials.
                response = {'ok': False, 'error': str(exc) if isinstance(exc, RuntimeError) else '后台组件调用失败，请检查窗口和插件设置'}
            print(json.dumps(response, ensure_ascii=True), flush=True)
    finally:
        if dm is not None:
            try:
                dm.UnBindWindow()
            except Exception:
                pass
        dm = None
        loader = None
        pythoncom.CoUninitialize()


if __name__ == '__main__':
    main()
