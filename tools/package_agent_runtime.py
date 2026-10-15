"""Build an offline Windows x64 model add-on without machine state or conversations."""
import argparse,hashlib,json,zipfile
from pathlib import Path
ROOT=Path(__file__).resolve().parents[1]
def digest(path):
    h=hashlib.sha256()
    with path.open('rb') as stream:
        for block in iter(lambda:stream.read(1024*1024),b''):h.update(block)
    return h.hexdigest()
def main():
    parser=argparse.ArgumentParser();parser.add_argument('--cpu-only',action='store_true');parser.add_argument('--output',type=Path)
    args=parser.parse_args();runtime=ROOT/'.agent-runtime'
    output=args.output or ROOT/'artifacts/dist'/('AnClicker-Agent-runtime-win-x64'+('-cpu' if args.cpu_only else '')+'.zip')
    output.parent.mkdir(parents=True,exist_ok=True)
    files=[runtime/'qwen2.5-0.5b-instruct-q4_0.gguf',runtime/'LICENSE-Qwen.txt',runtime/'LICENSE-llama.cpp.txt']
    for name in ['llama-cpu']+([] if args.cpu_only else ['llama-vulkan']):
        folder=runtime/name
        if not (folder/'llama-server.exe').is_file():raise FileNotFoundError(folder)
        files.extend(f for f in folder.rglob('*') if f.is_file())
    manifest={'kind':'local-model-addon','platform':'Windows 10/11 x64','model':'Qwen2.5-0.5B-Instruct Q4_0','runtime':'llama.cpp b11429','gpu':not args.cpu_only,'files':[]}
    notes='AnClicker 本机小模型离线运行包\n\n解压到带有“对话 Agent”页的 AnClicker.exe 旁；源码开发版则解压到项目根目录。应得到 .agent-runtime 文件夹。旧版没有 Agent 页面时，此包不会新增界面。\n支持 Windows 10/11 x64。GPU 使用 Vulkan，显卡不可用自动回退 CPU。权重约 429 MB；运行器、缓存和运行内存另计。\n打开对话 Agent，使用默认本机接口，发送消息即可启动。默认空闲 300 秒释放资源，下次请求自动唤醒；可在设置中指定 CPU/GPU 优先和空闲时间。\n本包不含聊天记录、服务 PID、密钥或用户数据库。\n'
    with zipfile.ZipFile(output,'x',compression=zipfile.ZIP_DEFLATED,compresslevel=1) as archive:
        for file in sorted(set(files)):
            relative='.agent-runtime/'+file.relative_to(runtime).as_posix()
            manifest['files'].append({'path':relative,'bytes':file.stat().st_size,'sha256':digest(file)})
            archive.write(file,relative)
        archive.writestr('模型包使用说明.txt',notes)
        archive.writestr('.agent-runtime/bundle-manifest.json',json.dumps(manifest,ensure_ascii=False,indent=2))
    with zipfile.ZipFile(output) as archive:
        bad=archive.testzip()
        if bad:raise RuntimeError('ZIP CRC failed: '+bad)
    sha=digest(output);output.with_suffix('.zip.sha256').write_text(sha+'  '+output.name+'\n',encoding='ascii')
    print(json.dumps({'path':str(output),'bytes':output.stat().st_size,'sha256':sha,'files':len(manifest['files'])},ensure_ascii=False))
if __name__=='__main__':main()
