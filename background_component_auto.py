"""Install the pinned background runtime on first use, outside replaceable app files."""
import hashlib
import json
import os
from pathlib import Path
import shutil
import sys
import tempfile
import threading
import time
from urllib.request import Request, urlopen

COMMIT = 'e393cee8b0798be4b4f6458b632192fc466f3af2'
SOURCE = 'https://raw.githubusercontent.com/yuan71058/dm72424-go/' + COMMIT + '/DM-DLL/'
FILES = (
    ('xd47243.dll', 9822396, 'dll_sha256'),
    ('Go.dll', 2842624, 'helper_sha256'),
)
_install_lock = threading.Lock()


class ConfigurationCancelled(RuntimeError):
    pass


class DownloadUnavailable(RuntimeError):
    pass


def _check_cancel(cancelled):
    if cancelled():
        raise ConfigurationCancelled('后台组件配置已取消')


def managed_directory():
    # prepare_environment also handles portable upgrades and unwritable installations.
    from startup_environment import prepare_environment
    return prepare_environment() / 'damo' / '7.2424'


def _hashes():
    return json.loads(Path(__file__).with_name('background_native_72424.json').read_text(encoding='utf8'))


def _valid(path, size, digest):
    try:
        if path.stat().st_size != size:
            return False
        checksum = hashlib.sha256()
        with path.open('rb') as stream:
            for block in iter(lambda: stream.read(1024 * 1024), b''):
                checksum.update(block)
        return checksum.hexdigest() == digest
    except OSError:
        return False


def _configuration(directory):
    return {
        'backend': 'native-7.2424',
        'dll_path': str((directory / 'xd47243.dll').resolve()),
        'helper_path': str((directory / 'Go.dll').resolve()),
    }


def _download_once(url, name, target, size, digest, emit, cancelled):
    request = Request(url, headers={'User-Agent': 'AnClicker-Component-Setup',
                                   'Accept': 'application/vnd.github.raw+json'})
    deadline = time.monotonic() + 120
    checksum = hashlib.sha256()
    received, last = 0, -1
    _check_cancel(cancelled)
    try:
        with urlopen(request, timeout=5) as response, target.open('wb') as output:
            if not response.geturl().startswith('https://'):
                raise RuntimeError('后台组件下载地址无效')
            while True:
                _check_cancel(cancelled)
                if time.monotonic() > deadline:
                    raise DownloadUnavailable('后台组件下载超时，请重试')
                block = response.read1(64 * 1024)
                if not block:
                    break
                received += len(block)
                if received > size:
                    raise RuntimeError('后台组件文件大小不符，已停止安装')
                checksum.update(block)
                output.write(block)
                percent = received * 100 // size
                if percent // 5 != last:
                    last = percent // 5
                    emit('正在下载后台组件 ' + name + '：' + str(percent) + '%')
    except ConfigurationCancelled:
        raise
    except (OSError, TimeoutError) as error:
        _check_cancel(cancelled)
        raise DownloadUnavailable('后台组件下载失败，请检查网络后重试；也可将配套组件放入 current/damo 后重试') from error
    _check_cancel(cancelled)
    if received != size or checksum.hexdigest() != digest:
        raise RuntimeError('后台组件校验失败，已停止安装；请重新配置')


def _download(name, target, size, digest, emit, cancelled):
    urls = (
        SOURCE + name,
        'https://api.github.com/repos/yuan71058/dm72424-go/contents/DM-DLL/' + name + '?ref=' + COMMIT,
    )
    for index, url in enumerate(urls):
        try:
            return _download_once(url, name, target, size, digest, emit, cancelled)
        except DownloadUnavailable:
            if index + 1 == len(urls):
                raise
            emit('当前下载连接不可用，正在切换备用下载地址…')
            _check_cancel(cancelled)


def ensure_component(*, emit=lambda message: None, cancelled=lambda: False):
    """Return a complete verified pair. Partial downloads are never loadable."""
    if sys.platform != 'win32':
        raise RuntimeError('大漠后台功能仅支持 Windows')
    from background_component_settings import config_path
    _check_cancel(cancelled)
    while not _install_lock.acquire(timeout=.1):
        _check_cancel(cancelled)
    try:
        _check_cancel(cancelled)
        directory = managed_directory()
        hashes = _hashes()
        expected = [(name, size, hashes[key]) for name, size, key in FILES]
        if all(_valid(directory / name, size, digest) for name, size, digest in expected):
            return _configuration(directory)
        directory.mkdir(parents=True, exist_ok=True)
        # Only known application locations, never a disk-wide scan or system DLL registration.
        app = Path(sys.executable).parent if getattr(sys, 'frozen', False) else Path(__file__).parent / 'current'
        local = (config_path().parent, app / 'damo')
        emit('正在自动配置后台组件…')
        with tempfile.TemporaryDirectory(prefix='.install-', dir=directory) as temporary:
            staging = Path(temporary)
            for name, size, digest in expected:
                _check_cancel(cancelled)
                source = next((folder / name for folder in (directory, *local)
                               if _valid(folder / name, size, digest)), None)
                target = staging / name
                if source is not None:
                    shutil.copyfile(source, target)
                else:
                    _download(name, target, size, digest, emit, cancelled)
                if not _valid(target, size, digest):
                    raise RuntimeError('后台组件校验失败，已停止安装')
                from background_dm_worker import pe_bits
                if pe_bits(target) != 32:
                    raise RuntimeError('后台组件位数不匹配，已停止安装')
            _check_cancel(cancelled)
            for name, _, _ in expected:
                os.replace(staging / name, directory / name)
            receipt = {
                'version': '7.2424', 'source': SOURCE, 'commit': COMMIT,
                'files': {name: digest for name, _, digest in expected},
            }
            stamp = staging / 'installed.json'
            stamp.write_text(json.dumps(receipt, ensure_ascii=False, indent=2), encoding='utf8')
            os.replace(stamp, directory / 'installed.json')
        emit('后台组件已自动配置，下次使用无需重复下载')
        return _configuration(directory)
    finally:
        _install_lock.release()


def resolved_config(*, automatic=True, emit=lambda message: None, cancelled=lambda: False):
    """Respect manual configuration; automatic installation is the clean-install default."""
    from background_component_settings import config_path, read_config
    path = config_path()
    config = read_config(path)
    if config.get('mode') != 'auto' and (config.get('dll_path') or config.get('backend')):
        result = dict(config)
        for key in ('dll_path', 'helper_path'):
            if result.get(key) and not Path(result[key]).is_absolute():
                result[key] = str((path.parent / result[key]).resolve())
        return result
    # Preserve the traditional dm.dll-only COM setup.
    local_dll = path.parent / 'dm.dll'
    if not config and local_dll.is_file():
        return {'backend': 'com', 'dll_path': str(local_dll.resolve())}
    return ensure_component(emit=emit, cancelled=cancelled) if automatic else {}
