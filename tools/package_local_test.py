
import sys as _import_sys
from pathlib import Path as _ImportPath
if __package__ in (None, ""):
    _import_sys.path.insert(0, str(_ImportPath(__file__).resolve().parents[1]))
from anclicker._imports import DeferredImports as _DeferredImports

# Dependencies declared here retain their existing on-demand loading boundaries.
_module_imports = _DeferredImports(globals(), {
    'hashlib': ('import', 'hashlib', (), False),
    'json': ('import', 'json', (), False),
    'zipfile': ('import', 'zipfile', (), False),
    'sys': ('import', 'sys', (), False),
    'Path': ('from', 'pathlib', ('Path',), 0),
    'CURRENT_VERSION_APP_ID_EXECUTABLE_NAME': ('from', 'info', ('CURRENT_VERSION', 'APP_ID', 'EXECUTABLE_NAME'), 0),
})

def main():
    """Create a local test ZIP only; no publishing or update-feed changes."""
    hashlib = _module_imports.load('hashlib'); json = _module_imports.load('json'); zipfile = _module_imports.load('zipfile'); sys = _module_imports.load('sys')
    Path = _module_imports.load('Path')
    root=Path(__file__).resolve().parents[1]
    sys.path.insert(0, str(root))
    CURRENT_VERSION, APP_ID, EXECUTABLE_NAME = _module_imports.load('CURRENT_VERSION_APP_ID_EXECUTABLE_NAME')
    source=root/'artifacts/dist/local-test'/APP_ID
    report=json.loads((root/'artifacts/validation/packaged-smoke/startup-ready.json').read_text(encoding='utf-8'))
    assert report['ready'] and report['rpa_validation']['browser'] and report['ocr_validation']['rapidocr']
    output=root/'artifacts/dist'/f'AnClicker-local-test-{CURRENT_VERSION}.zip'
    output.parent.mkdir(parents=True, exist_ok=True)
    if output.exists(): raise FileExistsError(output)
    notes=f'AnClicker {CURRENT_VERSION} 本地测试包\n完整解压后运行 {APP_ID}/{EXECUTABLE_NAME}。\n验证范围：Excel、流程执行、OCR、独立浏览器和 Agent 页面。\n仅本地构建，未上传或发布。\n'
    with zipfile.ZipFile(output,'x',compression=zipfile.ZIP_DEFLATED,compresslevel=6) as archive:
        for file in sorted(source.rglob('*')):
            if file.is_file(): archive.write(file,'AnClicker/'+file.relative_to(source).as_posix())
        archive.writestr('测试说明.txt',notes.encode('utf-8'))
        archive.writestr('BUILD-MANIFEST.json',json.dumps({'kind':'local-test','base_version':CURRENT_VERSION.removeprefix('v'),'python':report['runtime']['python'],'published':False,'exe_sha256':hashlib.sha256((source/EXECUTABLE_NAME).read_bytes()).hexdigest(),'checks':{'editors':report['editor_validation'],'ocr':report['ocr_validation'],'rpa':report['rpa_validation']}},ensure_ascii=False,indent=2))
    with zipfile.ZipFile(output) as archive:
        bad=archive.testzip()
        if bad: raise RuntimeError(bad)
    digest=hashlib.sha256(output.read_bytes()).hexdigest()
    output.with_suffix('.zip.sha256').write_text(digest+'  '+output.name+'\n',encoding='ascii')
    print(json.dumps({'path':str(output),'size_mb':round(output.stat().st_size/1024/1024,1),'sha256':digest},ensure_ascii=True))
    

if __name__ == '__main__':
    main()
