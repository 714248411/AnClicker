"""Build the small Windows self-extracting project launcher."""
import hashlib,json,os,subprocess,tempfile
from pathlib import Path

def ensure_launcher(root):
    root=Path(root)
    folder=root/'resources/standalone'
    source=folder/'launcher.cs'
    target=folder/'launcher.exe'
    receipt=folder/'launcher-build.json'
    icon=root/'resources/clicker.ico'
    manifest=root/'tools/packaging/windows.manifest'
    identity=hashlib.sha256(source.read_bytes()+icon.read_bytes()+manifest.read_bytes()).hexdigest()
    if target.is_file() and receipt.is_file():
        saved=json.loads(receipt.read_text(encoding='utf8'))
        if saved.get('source')==identity and saved.get('exe')==hashlib.sha256(target.read_bytes()).hexdigest():
            return target
    framework=Path(os.environ.get('SystemRoot','C:/Windows'))/'Microsoft.NET/Framework64/v4.0.30319'
    compiler=framework/'csc.exe'
    if not compiler.is_file():raise RuntimeError('缺少 Windows .NET Framework C# 编译器，无法构建单文件启动器。')
    with tempfile.TemporaryDirectory(prefix='ac-launcher-build-') as temp:
        output=Path(temp)/'launcher.exe'
        command=[str(compiler),'/nologo','/target:winexe','/platform:x64','/optimize+',
                 '/out:'+str(output),'/win32icon:'+str(icon),'/win32manifest:'+str(manifest),
                 '/reference:System.Windows.Forms.dll',
                 '/reference:'+str(framework/'System.IO.Compression.dll'),
                 '/reference:'+str(framework/'System.IO.Compression.FileSystem.dll'),str(source)]
        result=subprocess.run(command,capture_output=True,creationflags=getattr(subprocess,'CREATE_NO_WINDOW',0))
        if result.returncode:
            raise RuntimeError('单文件启动器构建失败：'+(result.stdout+result.stderr).decode('utf8',errors='replace'))
        content=output.read_bytes()
        target.write_bytes(content)
        receipt.write_text(json.dumps({'source':identity,'exe':hashlib.sha256(content).hexdigest()}),encoding='utf8')
    return target

if __name__=='__main__':
    print(ensure_launcher(Path(__file__).resolve().parents[2]))
