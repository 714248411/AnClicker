from pathlib import Path
from PyInstaller.archive.readers import CArchiveReader
import types
root=Path(__file__).resolve().parents[1]
archive=CArchiveReader(str(root/'dist/velopack/AnClicker/AnClicker.exe'))
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
