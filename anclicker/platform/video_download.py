"""Cancellable, atomic download of directly accessible web video files."""
import os
import ipaddress
import tempfile
from pathlib import Path
from urllib.parse import urlsplit
import requests


def download_video(url, destination, referer='', cancelled=lambda: False):
    def validate(address):
        parts = urlsplit(address)
        if parts.scheme not in ('http', 'https') or not parts.netloc:
            raise ValueError('仅支持直接访问的视频文件；临时地址无法另存')
        if parts.path.lower().endswith(('.m3u8', '.mpd')):
            raise ValueError('此视频是分段流，暂不支持直接另存')
    validate(url)
    target = Path(destination)
    temporary = None
    try:
        with requests.Session() as session:
            headers = {'User-Agent': 'Mozilla/5.0', 'Accept-Encoding': 'identity'}
            if referer:
                headers['Referer'] = referer
            for _ in range(10):
                if cancelled():
                    raise InterruptedError('已取消下载')
                hostname = urlsplit(url).hostname or ''
                try:
                    local = ipaddress.ip_address(hostname).is_loopback
                except ValueError:
                    local = hostname.lower() == 'localhost'
                # Local browser/test resources must not be sent to a system proxy.
                proxies = {'http': '', 'https': '', 'all': ''} if local else None
                response = session.get(url, headers=headers, stream=True, timeout=(10, 10),
                                       allow_redirects=False, proxies=proxies)
                if response.is_redirect:
                    from urllib.parse import urljoin
                    next_url = urljoin(url, response.headers.get('Location', ''))
                    response.close()
                    validate(next_url)
                    url = next_url
                    continue
                break
            else:
                raise ValueError('视频地址重定向次数过多')
            with response:
                response.raise_for_status()
                mime = response.headers.get('Content-Type', '').split(';')[0].lower()
                if mime in ('application/vnd.apple.mpegurl', 'application/x-mpegurl', 'application/dash+xml') or mime.startswith(('text/', 'application/json')):
                    raise ValueError('该地址返回网页或分段播放列表，无法保存为视频')
                fd, temporary = tempfile.mkstemp(prefix='.video-', suffix='.part', dir=str(target.parent))
                total = 0
                with os.fdopen(fd, 'wb') as output:
                    for chunk in response.iter_content(64 * 1024):
                        if cancelled():
                            raise InterruptedError('已取消下载')
                        if not chunk:
                            continue
                        if not total:
                            prefix = chunk.lstrip()[:256].lower()
                            valid = (chunk[4:8] == b'ftyp' or chunk[:4] == b'\x1aE\xdf\xa3' or chunk[:4] == b'OggS' or chunk[:3] == b'FLV' or chunk[:4] == b'RIFF' and chunk[8:12] == b'AVI ')
                            if not valid or prefix.startswith((b'<', b'#extm3u', b'{')):
                                raise ValueError('返回内容不是支持的视频文件，可能需要登录或不允许直接下载')
                        output.write(chunk)
                        total += len(chunk)
                if not total:
                    raise ValueError('视频内容为空')
                expected = response.headers.get('Content-Length')
                if expected and not response.headers.get('Content-Encoding') and total != int(expected):
                    raise ValueError('视频下载不完整，请重试')
                if cancelled():
                    raise InterruptedError('已取消下载')
                os.replace(temporary, target)
                temporary = None
                return target
    finally:
        if temporary:
            Path(temporary).unlink(missing_ok=True)
