"""Build-time PE checks, not a substitute for running Windows 10 1607."""
from pathlib import Path
import re
import hashlib
import json
import xml.etree.ElementTree as ET

import sys as _import_sys
from pathlib import Path as _ImportPath
if __package__ in (None, ""):
    _import_sys.path.insert(0, str(_ImportPath(__file__).resolve().parents[2]))
from anclicker._imports import DeferredImports as _DeferredImports

# Dependencies declared here retain their existing on-demand loading boundaries.
_module_imports = _DeferredImports(globals(), {
    'pefile': ('import', 'pefile', (), False),
})


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
    pefile = _module_imports.load('pefile')
    root = Path(app_dir)
    paths = sorted(p for p in root.rglob('*') if p.suffix.lower() in ('.exe', '.dll', '.pyd'))
    root_files = {p.name.casefold(): p for p in root.iterdir() if p.is_file()}
    os_runtime = [name for name in root_files
                  if name == 'ucrtbase.dll' or name.startswith(('api-ms-win-', 'ext-ms-win-'))]
    if os_runtime:
        raise RuntimeError('Do not bundle build-host Windows OS runtime DLLs: ' + ', '.join(os_runtime))
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
    isolated_x86 = {
        "resources/background/dll/xd47243.dll": "dll_sha256",
        "resources/background/dll/go.dll": "helper_sha256",
    }
    imports_checked = 0
    for path in paths:
        relative = path.relative_to(root).as_posix().casefold()
        template_prefix = 'runtime/crawl4ai/python/lib/site-packages/'
        launcher_templates = {
            'pip/_vendor/distlib/t32.exe', 'pip/_vendor/distlib/w32.exe',
            'pip/_vendor/distlib/t64-arm.exe', 'pip/_vendor/distlib/w64-arm.exe',
            'setuptools/cli-32.exe', 'setuptools/gui-32.exe',
            'setuptools/cli.exe', 'setuptools/gui.exe',
            'setuptools/cli-arm64.exe', 'setuptools/gui-arm64.exe',
        }
        # These are inert templates for generating scripts on other architectures,
        # not executables launched by the bundled x64 interpreter.
        if relative.startswith(template_prefix) and relative[len(template_prefix):] in launcher_templates:
            continue
        with pefile.PE(str(path), fast_load=True) as pe:
            if relative in isolated_x86:
                # These pinned DLLs run only in the separate SysWOW64 host.
                manifest = json.loads((root / 'resources/background/background_native_72424.json').read_text(encoding='utf8'))
                expected = manifest[isolated_x86[relative]]
                if pe.FILE_HEADER.Machine != 0x14c or hashlib.sha256(path.read_bytes()).hexdigest() != expected:
                    raise RuntimeError(f'Invalid isolated x86 background component: {path}')
                pe.parse_data_directories([1, 13])
                for entry in getattr(pe, 'DIRECTORY_ENTRY_IMPORT', []) + getattr(pe, 'DIRECTORY_ENTRY_DELAY_IMPORT', []):
                    if re.match(rb'^(msvcp|vcruntime|concrt)140.*[.]dll$', entry.dll.lower()):
                        raise RuntimeError(f'Isolated x86 component needs a separate x86 runtime: {path}')
                continue
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
                    # Wheels preload their package-specific sibling .libs folder.
                    # Do not accept arbitrary DLLs from elsewhere in the bundle.
                    for parent in path.parents:
                        if parent.name.casefold() == 'site-packages':
                            package = path.relative_to(parent).parts[0]
                            library = parent / (package + '.libs')
                            if library.is_dir():
                                dependency = next((p for p in library.iterdir() if p.name.casefold() == name), None)
                            break
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
