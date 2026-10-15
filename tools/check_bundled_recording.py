from pathlib import Path
from PyInstaller.archive.readers import CArchiveReader
import types

import sys as _import_sys
from pathlib import Path as _ImportPath
if __package__ in (None, ""):
    _import_sys.path.insert(0, str(_ImportPath(__file__).resolve().parents[1]))
from anclicker._imports import DeferredImports as _DeferredImports

# Dependencies declared here retain their existing on-demand loading boundaries.
_module_imports = _DeferredImports(globals(), {
    'sys': ('import', 'sys', (), False),
    'APP_ID_EXECUTABLE_NAME': ('from', 'info', ('APP_ID', 'EXECUTABLE_NAME'), 0),
})

root=Path(__file__).resolve().parents[1]
sys = _module_imports.load('sys')
sys.path.insert(0, str(root))
APP_ID, EXECUTABLE_NAME = _module_imports.load('APP_ID_EXECUTABLE_NAME')
archive=CArchiveReader(str(root/'artifacts/dist/velopack'/APP_ID/EXECUTABLE_NAME))
key=next(k for k in archive.toc if k.endswith('.pyz'))
pyz=archive.open_embedded_archive(key)
code=pyz.extract('rpa_validation')
def strings(code):
    for item in code.co_consts:
        if isinstance(item,str):yield item
        elif isinstance(item,types.CodeType):yield from strings(item)
assert 'acRecordStart' in set(strings(code))
assert 'web_recording_view' in pyz.toc
print('Packaged recording validation and UI are present')
