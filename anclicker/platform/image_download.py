"""Save original web images atomically without decoding them on the UI thread."""
import base64
import io
import os
import tempfile
from pathlib import Path
from urllib.parse import urlsplit, urljoin, unquote_to_bytes
import requests
from PIL import Image

LIMIT = 64 * 1024 * 1024
EXTENSIONS = {'PNG':'.png','JPEG':'.jpg','GIF':'.gif','WEBP':'.webp','BMP':'.bmp','TIFF':'.tiff','ICO':'.ico','AVIF':'.avif'}

def image_extension(data):
    # SVG is saved as source, never executed or rendered in this dialog.
    if data.lstrip().startswith(b'<'):
        import xml.etree.ElementTree as ET
        if b'<!DOCTYPE' in data.upper() or b'<!ENTITY' in data.upper():
            raise ValueError('不支持包含外部实体的图片')
        try:
            if ET.fromstring(data).tag.rsplit('}',1)[-1] == 'svg':return '.svg'
        except ET.ParseError:pass
        raise ValueError('地址返回了网页而不是图片，可能需要登录')
    try:
        with Image.open(io.BytesIO(data)) as image:
            suffix = EXTENSIONS.get(image.format)
            image.verify()
            if suffix:return suffix
    except (OSError, ValueError, Image.DecompressionBombError) as error:
        raise ValueError('图片内容无效或下载不完整') from error
    raise ValueError('暂不支持这种图片格式')

def download_image(url, destination, referer='', cancelled=lambda:False, progress=lambda done,total:None):
    def check():
        if cancelled():raise InterruptedError('已取消下载')
    def validate(address):
        if urlsplit(address).scheme not in ('http','https') or not urlsplit(address).netloc:
            raise ValueError('仅支持网页图片地址；临时 blob 图片需在浏览器中保存')
    check()
    if url.startswith('data:'):
        if len(url)>LIMIT*2:raise ValueError('图片超过 64 MB 限制')
        header, encoded = url.split(',',1)
        if not header.lower().startswith('data:image/'):raise ValueError('不是图片数据')
        data = base64.b64decode(encoded,validate=True) if ';base64' in header.lower() else unquote_to_bytes(encoded)
    else:
        url = urljoin(referer,url)
        validate(url)
        with requests.Session() as session:
            headers={'User-Agent':'Mozilla/5.0','Accept-Encoding':'identity'}
            if referer:headers['Referer']=referer
            for _ in range(10):
                check()
                import ipaddress
                hostname=urlsplit(url).hostname or ''
                try:local=ipaddress.ip_address(hostname).is_loopback
                except ValueError:local=hostname.lower()=='localhost'
                response=session.get(url,headers=headers,stream=True,timeout=(5,5),allow_redirects=False,
                    proxies={'http':'','https':'','all':''} if local else None)
                if response.is_redirect:
                    next_url=urljoin(url,response.headers.get('Location',''));response.close();validate(next_url);url=next_url
                else:break
            else:raise ValueError('图片地址重定向次数过多')
            with response:
                response.raise_for_status()
                expected=int(response.headers.get('Content-Length') or 0)
                if expected>LIMIT:raise ValueError('图片超过 64 MB 限制')
                chunks=[];total=0
                for chunk in response.iter_content(64*1024):
                    check()
                    total+=len(chunk)
                    if total>LIMIT:raise ValueError('图片超过 64 MB 限制')
                    chunks.append(chunk);progress(total,expected)
                if expected and not response.headers.get('Content-Encoding') and total!=expected:
                    raise ValueError('图片下载不完整，请重试')
                data=b''.join(chunks)
    check()
    if not data:raise ValueError('图片内容为空')
    if len(data)>LIMIT:raise ValueError('图片超过 64 MB 限制')
    suffix=image_extension(data)
    target=Path(destination)
    if not target.suffix:
        target=target.with_suffix(suffix)
        if target.exists():raise FileExistsError('目标文件已存在，请在另存为时填写完整文件名并确认覆盖：'+str(target))
    # Save original bytes, not a screenshot or an image URL list.
    temporary=None
    try:
        fd,temporary=tempfile.mkstemp(prefix='.image-',suffix='.part',dir=str(target.parent))
        with os.fdopen(fd,'wb') as output:output.write(data)
        check();os.replace(temporary,target);temporary=None
        progress(len(data),len(data))
        return target
    finally:
        if temporary:Path(temporary).unlink(missing_ok=True)
