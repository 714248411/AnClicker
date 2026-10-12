"""Build-time PE checks, not a substitute for running Windows 10 1607."""
from pathlib import Path
import re
import xml.etree.ElementTree as ET

RUNTIME_NAMES = ('msvcp140.dll', 'msvcp140_1.dll', 'msvcp140_2.dll',
                 'msvcp140_codecvt_ids.dll', 'concrt140.dll',
                 'vcruntime140.dll', 'vcruntime140_1.dll')


def validate_manifest(content):
    root = ET.fromstring(content)
    dpi = root.find('.//{http://schemas.microsoft.com/SMI/2016/WindowsSettings}dpiAwareness')
    values = [value.strip().casefold() for value in (dpi.text or '').split(',')] if dpi is not None else []
    if values != ['permonitorv2', 'permonitor']:
        raise RuntimeError('EXE manifest must retain the Windows 1607 PerMonitor fallback')


def validate_native_runtime(app_dir):
    import pefile
    root = Path(app_dir)
    paths = sorted(p for p in root.rglob('*') if p.suffix.lower() in ('.exe', '.dll', '.pyd'))
    root_files = {p.name.casefold(): p for p in root.iterdir() if p.is_file()}
    missing = set(RUNTIME_NAMES) - root_files.keys()
    if missing:
        raise RuntimeError('Missing app-local C++ runtime: ' + ', '.join(sorted(missing)))
    exports = {}
    def symbols(path):
        if path not in exports:
            with pefile.PE(str(path), fast_load=True) as pe:
                pe.parse_data_directories([0])
                entries = getattr(getattr(pe, 'DIRECTORY_ENTRY_EXPORT', None), 'symbols', [])
                exports[path] = {item.name if item.name else item.ordinal for item in entries}
                exports[path].update(item.ordinal for item in entries)
        return exports[path]
    imports_checked = 0
    for path in paths:
        with pefile.PE(str(path), fast_load=True) as pe:
            if pe.FILE_HEADER.Machine != 0x8664:
                raise RuntimeError(f'Non-x64 native binary: {path}')
            pe.parse_data_directories([1, 13])
            for entry in getattr(pe, 'DIRECTORY_ENTRY_IMPORT', []) + getattr(pe, 'DIRECTORY_ENTRY_DELAY_IMPORT', []):
                name = entry.dll.decode('ascii').casefold()
                if not re.match(r'^(msvcp|vcruntime|concrt)140.*[.]dll$', name):
                    continue
                dependency = root_files.get(name)
                if dependency is None:
                    # delvewheel-renamed libraries keep their unique local name.
                    dependency = next((p for p in path.parent.iterdir() if p.name.casefold() == name), None)
                if dependency is None:
                    raise RuntimeError(f'{path}: missing runtime dependency {name}')
                available = symbols(dependency)
                for item in entry.imports:
                    symbol = item.name if item.name else item.ordinal
                    if symbol not in available:
                        raise RuntimeError(f'{path}: {name} lacks {symbol!r}')
                    imports_checked += 1
    executable = root / 'AnClicker.exe'
    with pefile.PE(str(executable), fast_load=True) as pe:
        pe.parse_data_directories([2])
        manifests = []
        for entry in pe.DIRECTORY_ENTRY_RESOURCE.entries:
            if entry.id == 24:
                for name in entry.directory.entries:
                    for language in name.directory.entries:
                        data = language.data.struct
                        manifests.append(pe.get_data(data.OffsetToData, data.Size))
        if len(manifests) != 1:
            raise RuntimeError('Expected one embedded application manifest')
        validate_manifest(manifests[0])
    return {'native_binaries': len(paths), 'runtime_symbols_checked': imports_checked,
            'target': 'Windows 10 1607+ x64', 'target_os_verified': False}
