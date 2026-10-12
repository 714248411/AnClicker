def main():
    """Create a local test ZIP only; no publishing or update-feed changes."""
    import hashlib,json,zipfile
    from pathlib import Path
    root=Path(__file__).resolve().parents[1]
    source=root/'dist/local-test/AnClicker'
    report=json.loads((root/'validation/packaged-smoke/startup-ready.json').read_text(encoding='utf-8'))
    assert report['ready'] and report['rpa_validation']['browser'] and report['ocr_validation']['rapidocr']
    output=root.parent/'AnClicker-local-test-20261012.zip'
    if output.exists(): raise FileExistsError(output)
    notes='AnClicker 本地测试版（基于 1.4.5 重建 Excel、白话与网页功能）\n完整解压后运行 AnClicker/AnClicker.exe，不要单独移动 EXE。\n程序标题仍沿用 v1.4.5；此包包含本次新功能，不是公开发布版本。\n内置网页窗口标题：极速网页AC。\n需要测试：Excel 读写保存、白话指令、网页输入点击、OCR 分组、快捷操作下拉栏。\nExcel 写入后执行保存Excel指令；在线OCR需配置原有服务。\n这是便携测试包，未上传或发布。\n'
    with zipfile.ZipFile(output,'x',compression=zipfile.ZIP_DEFLATED,compresslevel=6) as archive:
        for file in sorted(source.rglob('*')):
            if file.is_file(): archive.write(file,'AnClicker/'+file.relative_to(source).as_posix())
        archive.writestr('测试说明.txt',notes.encode('utf-8'))
        archive.writestr('BUILD-MANIFEST.json',json.dumps({'kind':'local-test','base_version':'1.4.5','python':report['runtime']['python'],'published':False,'exe_sha256':hashlib.sha256((source/'AnClicker.exe').read_bytes()).hexdigest(),'checks':{'editors':report['editor_validation'],'ocr':report['ocr_validation'],'rpa':report['rpa_validation']}},ensure_ascii=False,indent=2))
    with zipfile.ZipFile(output) as archive:
        bad=archive.testzip()
        if bad: raise RuntimeError(bad)
    digest=hashlib.sha256(output.read_bytes()).hexdigest()
    output.with_suffix('.zip.sha256').write_text(digest+'  '+output.name+'\n',encoding='ascii')
    print(json.dumps({'path':str(output),'size_mb':round(output.stat().st_size/1024/1024,1),'sha256':digest},ensure_ascii=True))
    

if __name__ == '__main__':
    main()
