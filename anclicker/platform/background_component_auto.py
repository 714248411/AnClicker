from anclicker.app.paths import get_install_folder
from anclicker.app.paths import resource_path
"""Install the bundled offline runtime outside replaceable app files."""
import hashlib
import json
import os
from pathlib import Path
import shutil
import sys
import tempfile
import threading

from anclicker._imports import DeferredImports as _DeferredImports

# Dependencies declared here retain their existing on-demand loading boundaries.
_module_imports = _DeferredImports(globals(), {
    'prepare_environment': ('from', 'anclicker.app.startup_environment', ('prepare_environment',), 0),
    'config_path': ('from', 'anclicker.platform.background_component_settings', ('config_path',), 0),
    'pe_bits': ('from', 'anclicker.platform.background_dm_worker', ('pe_bits',), 0),
    'config_path_read_config': ('from', 'anclicker.platform.background_component_settings', ('config_path', 'read_config'), 0),
})


COMMIT = 'e393cee8b0798be4b4f6458b632192fc466f3af2'
SOURCE = 'https://raw.githubusercontent.com/yuan71058/dm72424-go/' + COMMIT + '/DM-DLL/'
FILES = (
    ('xd47243.dll', 9822396, 'dll_sha256'),
    ('Go.dll', 2842624, 'helper_sha256'),
)
_install_lock = threading.Lock()


class ConfigurationCancelled(RuntimeError):
    pass


def _check_cancel(cancelled):
    if cancelled():
        raise ConfigurationCancelled('后台组件配置已取消')


def managed_directory():
    # prepare_environment also handles portable upgrades and unwritable installations.
    prepare_environment = _module_imports.load('prepare_environment')
    return prepare_environment() / 'damo' / '7.2424'


def _hashes():
    return json.loads(resource_path('resources', 'background', 'background_native_72424.json').read_text(encoding='utf8'))


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


def ensure_component(*, emit=lambda message: None, cancelled=lambda: False):
    """Return a complete verified local pair; never fetch code from the network."""
    if sys.platform != 'win32':
        raise RuntimeError('大漠后台功能仅支持 Windows')
    config_path = _module_imports.load('config_path')
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
        app = Path(sys.executable).parent if getattr(sys, 'frozen', False) else Path(get_install_folder()) / 'current'
        local = (resource_path('resources', 'background', 'dll'), config_path().parent, app / 'damo')
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
                    raise RuntimeError('随包后台组件缺失或损坏：' + name + '；请重新解压完整安装包，或在大漠组件设置中选择配套 DLL。不会联网下载。')
                if not _valid(target, size, digest):
                    raise RuntimeError('后台组件校验失败，已停止安装')
                pe_bits = _module_imports.load('pe_bits')
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
        emit('后台组件已自动配置，已使用本地离线 DLL')
        return _configuration(directory)
    finally:
        _install_lock.release()


def resolved_config(*, automatic=True, emit=lambda message: None, cancelled=lambda: False):
    """Respect manual configuration; automatic installation is the clean-install default."""
    config_path, read_config = _module_imports.load('config_path_read_config')
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
