"""Build verified Windows Portable releases and publish directly to Qiniu Kodo."""
from __future__ import annotations
import argparse
import hashlib
import json
import os
import re
import shutil
import subprocess
import sys
import tempfile
import time
import zipfile
from dataclasses import dataclass
from pathlib import Path
from urllib.parse import quote, urlsplit
import requests

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT))
sys.path.insert(0, str(Path(__file__).resolve().parent))
from info import (CURRENT_VERSION, APP_ID, EXECUTABLE_NAME, UPDATE_CONFIG, update_source_config)
from 发布门槛 import ReleaseContext, validate_release
DEFAULT_APP = ROOT / 'dist/velopack' / APP_ID


class ReleaseError(ValueError):
    """Safe maintainer-facing diagnostics, without SDK response bodies or tokens."""



def version_tuple(version):
    if not re.fullmatch(r'(0|[1-9]\d*)\.(0|[1-9]\d*)\.(0|[1-9]\d*)', str(version)):
        raise ReleaseError('版本必须是 major.minor.patch')
    return tuple(map(int, version.split('.')))


def digest(path):
    with Path(path).open('rb') as stream:
        checksum = hashlib.sha256()
        for chunk in iter(lambda: stream.read(1024 * 1024), b''):
            checksum.update(chunk)
        return checksum.hexdigest().upper()


def safe_filename(name):
    if not name or '/' in name or '\\' in name or ':' in name or name in ('.', '..'):
        raise ReleaseError('更新包文件名不安全')
    return name


@dataclass(frozen=True)
class PublishConfig:
    bucket: str
    region: str
    base_url: str
    prefix: str

    @classmethod
    def from_environment(cls):
        base = os.environ.get(UPDATE_CONFIG['public_base_url_env'], UPDATE_CONFIG['public_base_url']).strip().rstrip('/')
        parsed = urlsplit(base)
        if (parsed.scheme != 'https' or not parsed.netloc or parsed.username
                or parsed.password or parsed.query or parsed.fragment or parsed.path not in ('', '/')):
            raise ReleaseError('必须设置 QINIU_PUBLIC_BASE_URL 为可验证的公开 HTTPS 域名，不能带路径或凭据')
        prefix = os.environ.get(UPDATE_CONFIG['key_prefix_env'], UPDATE_CONFIG['key_prefix']).strip('/')
        if not prefix or any(p in ('', '.', '..') for p in prefix.split('/')) or '\\' in prefix:
            raise ReleaseError('七牛目录前缀不安全')
        return cls(os.environ.get(UPDATE_CONFIG['bucket_env'], UPDATE_CONFIG['bucket']),
                   os.environ.get(UPDATE_CONFIG['region_env'], UPDATE_CONFIG['region']), base, prefix)

    @property
    def source_url(self):
        return self.base_url + '/' + quote(self.prefix, safe='/')

    def key(self, name):
        return self.prefix + '/' + safe_filename(name)

    def url(self, name):
        return self.source_url + '/' + quote(safe_filename(name))


def get_feed(config):
    response = requests.get(config.url(UPDATE_CONFIG['feed_name']), params={'release_check': time.time_ns()}, timeout=(15, 60))
    if response.status_code == 404:
        return {'Assets': []}
    response.raise_for_status()  # TLS verification is never disabled.
    feed = response.json()
    if not isinstance(feed, dict) or not isinstance(feed.get('Assets'), list):
        raise ReleaseError('远程更新索引格式无效')
    return feed


def current_assets(feed, version=None):
    result = []
    for asset in feed.get('Assets', []):
        if asset.get('PackageId') != UPDATE_CONFIG['pack_id']:
            raise ReleaseError('更新索引包含其他项目')
        version_tuple(asset['Version'])
        safe_filename(asset['FileName'])
        if asset['Type'] not in ('Full', 'Delta'):
            raise ReleaseError('更新索引只能包含 Full/Delta')
        expected = f"{UPDATE_CONFIG['pack_id']}-{asset['Version']}-{UPDATE_CONFIG['runtime']}-{asset['Type'].lower()}.nupkg"
        if (asset['FileName'] != expected or type(asset.get('Size')) is not int
                or asset['Size'] <= 0 or not re.fullmatch(r'[0-9a-fA-F]{64}', str(asset.get('SHA256', '')))):
            raise ReleaseError('更新索引文件名、大小或哈希无效')
        if asset['Type'] in ('Full', 'Delta') and (version is None or asset['Version'] == version):
            result.append(asset)
    return result


def assert_newer(version, feed):
    target = version_tuple(version)
    assets = current_assets(feed)
    if any(version_tuple(a['Version']) >= target for a in assets):
        raise ReleaseError('待发布版本必须高于远程版本；已发布版本不能重用')


def verify_public(config, name, size, sha256):
    with requests.get(config.url(name), params={'verify': time.time_ns()}, stream=True, timeout=(15, 120)) as response:
        response.raise_for_status()
        total = 0
        checksum = hashlib.sha256()
        for chunk in response.iter_content(1024 * 1024):
            total += len(chunk)
            checksum.update(chunk)
        if total != size or checksum.hexdigest().upper() != sha256.upper():
            raise RuntimeError('公网更新包大小或 SHA-256 不匹配')


def check_source(config, path=None):
    expected = {'url': config.source_url, 'pack_id': UPDATE_CONFIG['pack_id'], 'runtime': UPDATE_CONFIG['runtime']}
    public = update_source_config() if path is None else json.loads(path.read_text(encoding='utf-8'))
    if public != expected:
        raise ReleaseError('客户端更新源与上传目标不一致，停止操作')


def build(config, output):
    check_source(config)
    if output.exists() and any(output.iterdir()):
        raise ReleaseError('输出目录必须为空，请使用新目录')
    version = CURRENT_VERSION.removeprefix('v')
    remote = get_feed(config)
    assert_newer(version, remote)
    with tempfile.TemporaryDirectory(prefix='anclicker-baseline-') as folder:
        command = [sys.executable, str(ROOT / 'packaging/build_velopack.py'), '--output', str(output)]
        full = [a for a in current_assets(remote) if a['Type'] == 'Full']
        if full:
            base = max(full, key=lambda a: version_tuple(a['Version']))
            target = Path(folder) / safe_filename(base['FileName'])
            with requests.get(config.url(target.name), stream=True, timeout=(15, 120)) as response:
                response.raise_for_status()
                with target.open('wb') as stream:
                    for chunk in response.iter_content(1024 * 1024):
                        stream.write(chunk)
            if target.stat().st_size != base['Size'] or digest(target) != base['SHA256'].upper():
                raise ReleaseError('远程 Full 基线大小或哈希不匹配')
            command.extend(['--base', str(target)])
        subprocess.run(command, cwd=ROOT, check=True)
    # Publish only this release's assets; preserve the baseline nupkg for delta checks.
    path = output / UPDATE_CONFIG['feed_name']
    feed = json.loads(path.read_text(encoding='utf-8-sig'))
    feed['Assets'] = current_assets(feed, version)
    path.write_text(json.dumps(feed, ensure_ascii=False, indent=2), encoding='utf-8')
    validate_local(config, output, DEFAULT_APP)
    print('本地发布准备完成:', output)


def validate_local(config, release, app):
    from validation_cache import verify_once
    check_source(config)
    context = ReleaseContext(ROOT, app, release, release / UPDATE_CONFIG['portable_name'],
                             APP_ID, UPDATE_CONFIG['pack_id'], CURRENT_VERSION.removeprefix('v'), UPDATE_CONFIG['runtime'])
    verify_once(context, 'publish', lambda: _validate_local(config, release, app))
    feed = json.loads((release / UPDATE_CONFIG['feed_name']).read_text(encoding='utf-8-sig'))
    return feed, current_assets(feed, context.version)


def _validate_local(config, release, app):
    check_source(config)
    version = CURRENT_VERSION.removeprefix('v')
    version_tuple(version)
    from PyInstaller.archive.readers import CArchiveReader
    archive_reader = CArchiveReader(str(app / EXECUTABLE_NAME))
    pyz_names = [name for name in archive_reader.toc if name.lower().endswith('.pyz')]
    if len(pyz_names) != 1:
        raise ReleaseError('无法确认客户端 Python 模块清单')
    modules = archive_reader.open_embedded_archive(pyz_names[0]).toc
    if any(name == 'qiniu' or name.startswith('qiniu.') or '发布Velopack' in name for name in modules):
        raise ReleaseError('客户端包含发布专用模块')
    public = json.loads((app / UPDATE_CONFIG['snapshot_name']).read_text(encoding='utf-8'))
    if public != {'url': config.source_url, 'pack_id': UPDATE_CONFIG['pack_id'], 'runtime': UPDATE_CONFIG['runtime']}:
        raise ReleaseError('客户端更新源与发布目标不同，请重新构建')
    path = release / UPDATE_CONFIG['feed_name']
    feed = json.loads(path.read_text(encoding='utf-8-sig'))
    assets = current_assets(feed, version)
    if len(assets) != len(feed['Assets']) or sum(a['Type'] == 'Full' for a in assets) != 1:
        raise ReleaseError('本地 feed 必须仅引用当前版本且有一个 Full')
    if len({a['FileName'] for a in assets}) != len(assets):
        raise ReleaseError('本地 feed 文件重复')
    for asset in assets:
        package = release / safe_filename(asset['FileName'])
        expected_name = f"{UPDATE_CONFIG['pack_id']}-{version}-{UPDATE_CONFIG['runtime']}-{asset['Type'].lower()}.nupkg"
        if package.name != expected_name or package.stat().st_size != asset['Size'] or digest(package) != asset['SHA256'].upper():
            raise ReleaseError('本地更新包名称、大小或 SHA-256 不匹配')
    portable = list(release.glob('*-Portable.zip'))
    if len(portable) != 1:
        raise ReleaseError('必须有一个 Portable ZIP')
    # Ensure actual distributed application files are identical to the onedir validated build.
    full = release / next(a['FileName'] for a in assets if a['Type'] == 'Full')
    with zipfile.ZipFile(full) as archive:
        content = {n[8:]: n for n in archive.namelist() if n.startswith('lib/app/') and not n.endswith('/')}
        expected = {p.relative_to(app).as_posix(): p for p in app.rglob('*') if p.is_file()}
        if set(content) - set(expected) != {'sq.version', f'{APP_ID}_ExecutionStub.exe', 'Squirrel.exe'} or set(expected) - set(content) or any(archive.read(content[n]) != p.read_bytes() for n, p in expected.items()):
            raise ReleaseError('Full 与当前已验证构建不一致')
        import xml.etree.ElementTree as ET
        metadata = ET.fromstring(archive.read(content['sq.version']))
        fields = {node.tag.split('}')[-1]: node.text for node in metadata.iter()}
        if any(fields.get(k) != v for k, v in {'id': UPDATE_CONFIG['pack_id'], 'version': version, 'channel': UPDATE_CONFIG['runtime'], 'rid': UPDATE_CONFIG['runtime']}.items()):
            raise ReleaseError('Full 内版本元数据不匹配')
    with zipfile.ZipFile(portable[0]) as archive:
        names = set(archive.namelist())
        if not {'.portable', 'Update.exe', UPDATE_CONFIG['launcher_name'], 'current/sq.version'}.issubset(names):
            raise ReleaseError('Portable 结构不完整')
        for name, path in expected.items():
            if archive.read('current/' + name) != path.read_bytes():
                raise ReleaseError('Portable 与当前已验证构建不一致')
    validate_release(ReleaseContext(ROOT, app, release, portable[0], APP_ID, UPDATE_CONFIG['pack_id'], version, UPDATE_CONFIG['runtime']))
    return feed, assets


class QiniuUploader:
    def __init__(self, config):
        access = os.environ.get(UPDATE_CONFIG['access_key_env'], '').strip()
        secret = os.environ.get(UPDATE_CONFIG['secret_key_env'], '').strip()
        if not access or not secret:
            raise ReleaseError('发布必须设置 QINIU_ACCESS_KEY 和 QINIU_SECRET_KEY')
        import qiniu
        self.sdk = qiniu
        self.auth = qiniu.Auth(access, secret)
        self.config = config
        # Pin upload geography; discover bucket details to reject configuration mistakes.
        from qiniu.http.endpoint import Endpoint
        from qiniu.http.regions_provider import QueryRegionsProvider
        self.regions = QueryRegionsProvider(access_key=access, bucket_name=config.bucket,
            endpoints_provider=[Endpoint.from_host('https://uc.qiniuapi.com')], preferred_scheme='https')
        self.manager = qiniu.BucketManager(self.auth, preferred_scheme='https', regions=self.regions)
        details, info = self.manager.bucket_info(config.bucket)
        if info.status_code != 200 or details.get('region') != config.region or details.get('private') != 0:
            raise ReleaseError('七牛桶区域或公有属性与配置不一致')

    def upload(self, path, overwrite=False):
        config = self.config
        key = config.key(path.name)
        existing, status = self.manager.stat(config.bucket, key)
        checksum = self.sdk.etag(str(path))
        if status.status_code == 200 and not overwrite:
            if existing['fsize'] != path.stat().st_size or existing['hash'] != checksum:
                raise ReleaseError('同名远程版本包已存在且内容不同，请使用新版本')
            return
        if status.status_code not in (200, 612):
            raise RuntimeError('七牛对象状态检查失败')
        token = self.auth.upload_token(config.bucket, key, 3600,
            {'insertOnly': 0 if overwrite else 1})
        result, info = self.sdk.put_file(token, key, str(path), check_crc=True,
                                      version='v2', regions=self.regions)
        if info.status_code != 200 or not result or result.get('hash') != checksum:
            raise RuntimeError('七牛上传或内容校验失败')

    def refresh_feed(self):
        cdn = self.sdk.CdnManager(self.auth)
        cdn.server = 'https://fusion.qiniuapi.com'
        result, info = cdn.refresh_urls([self.config.url(UPDATE_CONFIG['feed_name'])])
        if info.status_code != 200 or not result or result.get('code') != 200:
            raise RuntimeError('CDN 更新索引刷新失败；feed 可能已写入，请核验后恢复')


def publish(config, release, app):
    feed, assets = validate_local(config, release, app)
    assert_newer(CURRENT_VERSION.removeprefix('v'), get_feed(config))
    uploader = QiniuUploader(config)
    for asset in assets:
        path = release / asset['FileName']
        print('上传更新包:', path.name, flush=True)
        uploader.upload(path)
        print('公网下载校验:', path.name, flush=True)
        verify_public(config, path.name, asset['Size'], asset['SHA256'])
    # Recheck before the only mutable public object is replaced.
    assert_newer(CURRENT_VERSION.removeprefix('v'), get_feed(config))
    path = release / UPDATE_CONFIG['feed_name']
    if json.loads(path.read_text(encoding='utf-8-sig')) != feed:
        raise ReleaseError('发布过程中 feed 被修改，停止发布')
    try:
        print('发布更新索引并刷新 CDN。', flush=True)
        uploader.upload(path, overwrite=True)
        uploader.refresh_feed()
        for attempt in range(6):
            if get_feed(config) == feed:
                # Also verify the exact URL used by clients, without a cache-busting parameter.
                response = requests.get(config.url(UPDATE_CONFIG['feed_name']), timeout=(15, 60))
                response.raise_for_status()
                if response.json() == feed:
                    print('七牛直连发布完成:', config.url(UPDATE_CONFIG['feed_name']))
                    return
            time.sleep(5)
        raise RuntimeError('feed 公网验证未完成，可能已写入；不得重复覆盖，请检查 CDN 与远程版本')


    except Exception:
        raise ReleaseError('索引可能已对用户可见，但刷新或公网核验未完成。请核对云端状态，不要重建或覆盖同版本。') from None


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('command', choices=['build', 'publish'])
    parser.add_argument('--output', type=Path, required=True)
    parser.add_argument('--app-dir', type=Path, default=DEFAULT_APP)
    parser.add_argument('--publish', action='store_true')
    parser.add_argument('--yes', action='store_true')
    args = parser.parse_args()
    if (args.command == 'publish' or args.publish) and not args.yes:
        parser.error('发布需要显式 --yes')
    if args.command == 'build' and args.app_dir.resolve() != DEFAULT_APP.resolve():
        parser.error('--app-dir 仅适用于发布已有构建')
    config = PublishConfig.from_environment()
    if args.command == 'build':
        build(config, args.output.resolve())
    if args.command == 'publish' or args.publish:
        publish(config, args.output.resolve(), args.app_dir.resolve())


if __name__ == '__main__':
    try:
        main()
    except Exception as error:
        # SDK exceptions may contain signed URLs; never print their raw text.
        print(f'操作失败 ({type(error).__name__})。检查配置、产物及公网状态；未确认发布成功。', file=sys.stderr)
        if isinstance(error, ReleaseError):
            print(str(error), file=sys.stderr)
        raise SystemExit(1)
