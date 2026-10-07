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
from info import CURRENT_VERSION
from update.config import PACK_ID, RUNTIME, FEED_NAME
from 发布门槛 import ReleaseContext, validate_release
RELEASE = ROOT / 'dist' / 'velopack' / RUNTIME
APP = ROOT / 'dist' / 'AnClicker'


class ReleaseError(ValueError):
    """Safe maintainer-facing diagnostics, without SDK response bodies or tokens."""



def version_tuple(version):
    if not re.fullmatch(r'(0|[1-9]\d*)\.(0|[1-9]\d*)\.(0|[1-9]\d*)', str(version)):
        raise ReleaseError('版本必须是 major.minor.patch')
    return tuple(map(int, version.split('.')))


def digest(path):
    with Path(path).open('rb') as stream:
        return hashlib.file_digest(stream, 'sha256').hexdigest().upper()


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
        base = os.environ.get('QINIU_PUBLIC_BASE_URL', '').strip().rstrip('/')
        parsed = urlsplit(base)
        if (parsed.scheme != 'https' or not parsed.netloc or parsed.username
                or parsed.password or parsed.query or parsed.fragment or parsed.path not in ('', '/')):
            raise ReleaseError('必须设置 QINIU_PUBLIC_BASE_URL 为可验证的公开 HTTPS 域名，不能带路径或凭据')
        prefix = os.environ.get('QINIU_KEY_PREFIX', 'an-clicker/win-x64').strip('/')
        if not prefix or any(p in ('', '.', '..') for p in prefix.split('/')) or '\\' in prefix:
            raise ReleaseError('七牛目录前缀不安全')
        return cls(os.environ.get('QINIU_BUCKET', 'ytsoftware-velopack'),
                   os.environ.get('QINIU_REGION', 'z0'), base, prefix)

    @property
    def source_url(self):
        return self.base_url + '/' + quote(self.prefix, safe='/')

    def key(self, name):
        return self.prefix + '/' + safe_filename(name)

    def url(self, name):
        return self.source_url + '/' + quote(safe_filename(name))


def get_feed(config):
    response = requests.get(config.url(FEED_NAME), params={'release_check': time.time_ns()}, timeout=(15, 60))
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
        if asset.get('PackageId') != PACK_ID:
            raise ReleaseError('更新索引包含其他项目')
        version_tuple(asset['Version'])
        safe_filename(asset['FileName'])
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


def run(arguments, env=None):
    subprocess.run(arguments, cwd=ROOT, env=env, check=True)


def isolated_environment():
    env = os.environ.copy()
    system = Path(env.get('SystemRoot', r'C:\Windows'))
    env['PATH'] = os.pathsep.join(map(str, (Path(sys.executable).parent, Path(sys.base_prefix), system / 'System32', system)))
    # Build processes have no reason to receive publisher secrets.
    for key in ('QINIU_ACCESS_KEY', 'QINIU_SECRET_KEY'):
        env.pop(key, None)
    return env


def build(config):
    if sys.platform != 'win32' or __import__('struct').calcsize('P') != 8:
        raise ReleaseError('Velopack 构建要求 Windows x64 Python')
    version = CURRENT_VERSION.removeprefix('v')
    remote = get_feed(config)
    assert_newer(version, remote)
    if not RELEASE.resolve().is_relative_to(ROOT.resolve()):
        raise ReleaseError('构建输出目录必须位于当前项目内')
    if RELEASE.exists():
        shutil.rmtree(RELEASE)  # constant output path, never derived from credentials or user data
    RELEASE.mkdir(parents=True)
    run(['dotnet', 'tool', 'restore'], isolated_environment())
    # Fetch precisely the latest full baseline, checked against its public feed.
    full = [a for a in current_assets(remote) if a['Type'] == 'Full']
    if full:
        base = max(full, key=lambda a: version_tuple(a['Version']))
        name = safe_filename(base['FileName'])
        target = RELEASE / name
        with requests.get(config.url(name), stream=True, timeout=(15, 120)) as response:
            response.raise_for_status()
            with target.open('wb') as output:
                for chunk in response.iter_content(1024 * 1024):
                    output.write(chunk)
        if target.stat().st_size != base['Size'] or digest(target) != base['SHA256'].upper():
            raise RuntimeError('上一版 Full 校验失败')
    with tempfile.TemporaryDirectory(prefix='anclicker-build-config-') as folder:
        source = Path(folder) / 'update-source.json'
        source.write_text(json.dumps({'url': config.source_url, 'pack_id': PACK_ID, 'runtime': RUNTIME}), encoding='utf-8')
        env = isolated_environment()
        env['ANCLICKER_BUILD_UPDATE_SOURCE'] = str(source)
        run([sys.executable, '-m', 'PyInstaller', '--clean', '-y', 'packaging/main.spec'], env)
    run(['dotnet', 'tool', 'run', 'vpk', 'pack', '--packId', PACK_ID, '--packVersion', version,
         '--packDir', str(APP), '--mainExe', 'AnClicker.exe', '--packTitle', 'An Clicker',
         '--packAuthors', 'An Clicker contributors', '--channel', RUNTIME, '--runtime', RUNTIME,
         '--noInst', '--releaseNotes', str(ROOT / 'packaging/RELEASE_NOTES.md'),
         '--outputDir', str(RELEASE)], isolated_environment())
    # Keep only current release assets in the public feed, baselines remain local for validation.
    feed_path = RELEASE / FEED_NAME
    feed = json.loads(feed_path.read_text(encoding='utf-8-sig'))
    feed['Assets'] = current_assets(feed, version)
    feed_path.write_text(json.dumps(feed, ensure_ascii=False, indent=2), encoding='utf-8')
    validate_local(config)
    print('本地构建与发布门槛完成:', RELEASE)


def validate_local(config):
    version = CURRENT_VERSION.removeprefix('v')
    version_tuple(version)
    public = json.loads((APP / 'update-source.json').read_text(encoding='utf-8'))
    if public != {'url': config.source_url, 'pack_id': PACK_ID, 'runtime': RUNTIME}:
        raise ReleaseError('客户端更新源与发布目标不同，请重新构建')
    path = RELEASE / FEED_NAME
    feed = json.loads(path.read_text(encoding='utf-8-sig'))
    assets = current_assets(feed, version)
    if len(assets) != len(feed['Assets']) or sum(a['Type'] == 'Full' for a in assets) != 1:
        raise ReleaseError('本地 feed 必须仅引用当前版本且有一个 Full')
    if len({a['FileName'] for a in assets}) != len(assets):
        raise ReleaseError('本地 feed 文件重复')
    for asset in assets:
        package = RELEASE / safe_filename(asset['FileName'])
        expected_name = f"{PACK_ID}-{version}-{RUNTIME}-{asset['Type'].lower()}.nupkg"
        if package.name != expected_name or package.stat().st_size != asset['Size'] or digest(package) != asset['SHA256'].upper():
            raise ReleaseError('本地更新包名称、大小或 SHA-256 不匹配')
    portable = list(RELEASE.glob('*-Portable.zip'))
    if len(portable) != 1:
        raise ReleaseError('必须有一个 Portable ZIP')
    # Ensure actual distributed application files are identical to the onedir validated build.
    full = RELEASE / next(a['FileName'] for a in assets if a['Type'] == 'Full')
    with zipfile.ZipFile(full) as archive:
        content = {n[8:]: n for n in archive.namelist() if n.startswith('lib/app/') and not n.endswith('/')}
        expected = {p.relative_to(APP).as_posix(): p for p in APP.rglob('*') if p.is_file()}
        if set(content) - set(expected) != {'sq.version', 'AnClicker_ExecutionStub.exe', 'Squirrel.exe'} or set(expected) - set(content) or any(archive.read(content[n]) != p.read_bytes() for n, p in expected.items()):
            raise ReleaseError('Full 与当前已验证构建不一致')
        import xml.etree.ElementTree as ET
        metadata = ET.fromstring(archive.read(content['sq.version']))
        fields = {node.tag.split('}')[-1]: node.text for node in metadata.iter()}
        if any(fields.get(k) != v for k, v in {'id': PACK_ID, 'version': version, 'channel': RUNTIME, 'rid': RUNTIME}.items()):
            raise ReleaseError('Full 内版本元数据不匹配')
    with zipfile.ZipFile(portable[0]) as archive:
        names = set(archive.namelist())
        if not {'.portable', 'Update.exe', 'An Clicker.exe', 'current/sq.version'}.issubset(names):
            raise ReleaseError('Portable 结构不完整')
        for name, path in expected.items():
            if archive.read('current/' + name) != path.read_bytes():
                raise ReleaseError('Portable 与当前已验证构建不一致')
    validate_release(ReleaseContext(ROOT, APP, RELEASE, portable[0], 'AnClicker', PACK_ID, version, RUNTIME))
    return feed, assets


class QiniuUploader:
    def __init__(self, config):
        access = os.environ.get('QINIU_ACCESS_KEY', '').strip()
        secret = os.environ.get('QINIU_SECRET_KEY', '').strip()
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
        result, info = cdn.refresh_urls([self.config.url(FEED_NAME)])
        if info.status_code != 200 or not result or result.get('code') != 200:
            raise RuntimeError('CDN 更新索引刷新失败；feed 可能已写入，请核验后恢复')


def publish(config):
    feed, assets = validate_local(config)
    assert_newer(CURRENT_VERSION.removeprefix('v'), get_feed(config))
    uploader = QiniuUploader(config)
    for asset in assets:
        path = RELEASE / asset['FileName']
        uploader.upload(path)
        verify_public(config, path.name, asset['Size'], asset['SHA256'])
    # Recheck before the only mutable public object is replaced.
    assert_newer(CURRENT_VERSION.removeprefix('v'), get_feed(config))
    path = RELEASE / FEED_NAME
    if json.loads(path.read_text(encoding='utf-8-sig')) != feed:
        raise ReleaseError('发布过程中 feed 被修改，停止发布')
    uploader.upload(path, overwrite=True)
    uploader.refresh_feed()
    for attempt in range(6):
        if get_feed(config) == feed:
            # Also verify the exact URL used by clients, without a cache-busting parameter.
            response = requests.get(config.url(FEED_NAME), timeout=(15, 60))
            response.raise_for_status()
            if response.json() == feed:
                print('七牛直连发布完成:', config.url(FEED_NAME))
                return
        time.sleep(5)
    raise RuntimeError('feed 公网验证未完成，可能已写入；不得重复覆盖，请检查 CDN 与远程版本')


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('command', choices=['build', 'publish'])
    parser.add_argument('--publish', action='store_true')
    parser.add_argument('--yes', action='store_true')
    args = parser.parse_args()
    if (args.command == 'publish' or args.publish) and not args.yes:
        parser.error('发布需要显式 --yes')
    config = PublishConfig.from_environment()
    if args.command == 'build':
        build(config)
    if args.command == 'publish' or args.publish:
        publish(config)


if __name__ == '__main__':
    try:
        main()
    except Exception as error:
        # SDK exceptions may contain signed URLs; never print their raw text.
        print(f'操作失败 ({type(error).__name__})。检查配置、产物及公网状态；未确认发布成功。', file=sys.stderr)
        if isinstance(error, ReleaseError):
            print(str(error), file=sys.stderr)
        raise SystemExit(1)
