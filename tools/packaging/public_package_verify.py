"""Verify every public byte with bounded, retryable range requests."""
import hashlib,time
import requests

def verify_public_package(url,size,sha256,*,chunk_size=16*1024*1024):
    digest=hashlib.sha256();stamp=time.time_ns()
    for start in range(0,size,chunk_size):
        end=min(start+chunk_size,size)-1
        for attempt in range(3):
            try:
                with requests.get(url,params={'verify':stamp},headers={'Range':f'bytes={start}-{end}','Accept-Encoding':'identity'},stream=True,timeout=(15,60)) as response:
                    response.raise_for_status()
                    # Some servers ignore Range; only accept an entire verified
                    # response from byte zero, never append duplicate prefixes.
                    if response.status_code==200:
                        if start:raise RuntimeError('公网服务器未遵守续传范围')
                        full=hashlib.sha256();total=0
                        for block in response.iter_content(1024*1024):
                            total+=len(block)
                            if total>size:raise RuntimeError('公网更新包大小不匹配')
                            full.update(block)
                        if total!=size or full.hexdigest().upper()!=sha256.upper():raise RuntimeError('公网更新包大小或 SHA-256 不匹配')
                        return
                    if response.status_code!=206 or response.headers.get('Content-Range')!=f'bytes {start}-{end}/{size}':
                        raise RuntimeError('公网更新包分段响应范围不匹配')
                    content=bytearray()
                    for block in response.iter_content(1024*1024):
                        content.extend(block)
                        if len(content)>end-start+1:raise RuntimeError('公网更新包分段大小不匹配')
                    if len(content)!=end-start+1:raise requests.exceptions.ChunkedEncodingError('Incomplete public range')
                    digest.update(content)
                break
            except requests.RequestException:
                if attempt==2:raise
                time.sleep(attempt+1)
        if end+1==size or (end+1)%(256*1024*1024)==0:
            print(f'公网已校验 {end+1} / {size} 字节',flush=True)
    if digest.hexdigest().upper()!=sha256.upper():raise RuntimeError('公网更新包 SHA-256 不匹配')
